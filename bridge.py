#!/usr/bin/env python3
"""Navi bridge — serves the Apex dashboard and gives it real
local powers.

Stdlib only. Endpoints:
  GET  /              the dashboard (app/index.html)
  GET  /api/status    backend, model, version, llamafile reachability
  GET  /api/update/check -> the Updater's real check: the newest
                      GitHub release on the install's channel
                      (stable = latest full release; edge = newest
                      incl. pre-releases; ?channel= overrides the
                      saved choice) compared against the VERSION
                      file, with the running version's own release
                      page riding along for the panel's dropdown;
                      a check that cannot complete answers
                      ok: False with the reason
  POST /api/settings/updater-channel {channel} -> persists the
                      Updater's Stable / Edge channel choice in
                      the config's updater block
  POST /api/update/apply -> starts the end-to-end apply: a worker
                      downloads the latest release's package zip
                      (unwrapping a gzip-wrapped payload first),
                      verifies it is an Apex package, stages it
                      under updates/<tag>/package, then hands the
                      install to a detached helper (written into
                      updates/<tag>/) that outlives this bridge,
                      runs the staged installer (never --fresh),
                      relaunches the app through start.sh, and
                      records the outcome in config/update-result.json
  GET  /api/update/result -> the apply's live record: the step it
                      is on while it runs, and afterwards either
                      the confirmed version before → after or the
                      failed step, its reason, and the manual
                      fallback (staged folder + install command)
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
  GET  /api/rag/readme?repo=<owner/name> -> a pack repo's
                      README as raw Markdown (the pack flip cards)
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
  POST /api/downloads/save {filename, dataBase64} -> writes a
                      download the dashboard fetched inside the
                      desktop shell (chip .png, export ZIP) into
                      ~/Downloads under a sanitized basename —
                      the shell's webview cannot save files itself
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
install directory before replacing files — and since build .91 that
stop is a proof, not a gesture: the bridge is found by pid file, by
the process holding this port, and by working directory, waited on
until it is gone and the port is free, escalated to a forced end if
it will not go politely, and the install aborts with the holder
named (and the exact kill command printed) if the port cannot be
cleared — because a fire-and-forget stop once stranded an update
behind a frozen bridge that only a reboot could clear. When this
bridge starts against an incumbent that answers nothing, it
resolves the holder from the socket itself (port_holder_pid) and
names that pid in its messages, pid file or no pid file. The model string sent to the llamafile is read
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
import datetime
import gzip
import hashlib
import http.client
import importlib.util
import io
import ipaddress
import calendar
import json
import math
import os
import re
import secrets
import select
import socket
import shutil
import ssl
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
SHIPPED_VERSION = "0.1.9"
SHIPPED_VERSION_STATUS = "edge"

# This build's stamp — the dashboard baked into the same package
# carries the identical value and compares it against /api/status.
BRIDGE_BUILD = "2026-11-10.93"
# Edge build sequence (build .86): this package is its Edge
# version's publication number SHIPPED_BUILD_SEQ — 0.1.9e
# Build 2. The Updater's third comparison tier reads it.
SHIPPED_BUILD_SEQ = 2
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
        return {
            "live": {"llamafile_endpoint": "http://localhost:8080/v1"},
            # Navi Mesh defaults (see the Mesh section below): an
            # absent mesh block reads as exactly this — master off,
            # borrowing on under the master (R1), lending off.
            "mesh": {
                "enabled": False,
                "role": "both",
                "nodeName": "",
                "borrow": {"enabled": True, "graceMs": 2000, "peers": []},
                "lend": {
                    "enabled": False,
                    "maxSharePercent": 25,
                    "maxGenerationsPerHour": 20,
                    "perPeerPerHour": 10,
                    "idleOnly": True,
                    "idleAfterSeconds": 60,
                },
                "port": 8765,
                "nodeId": "",
                "ledger": True,
                "ledgerInBackup": False,
            },
        }


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False


# --- Local server (build .59; fluid activation .61) ---------------
# Settings -> System's toggle: OFF (the default) the bridge binds
# 127.0.0.1:8675 exactly as it always has; ON it binds 0.0.0.0:8675
# at launch, so a phone or tablet on the same network can open the
# dashboard. The flag is read once, here at startup — a bind is
# never hot-swapped. Build .61 makes the flip itself do the
# restarting: saving the toggle records a restart request in the
# config block and this process exits with code 75, the handshake
# the launcher's supervise_bridge loop already relaunches on (the
# same one an install takeover uses). The relaunched bridge reads
# the saved flag, binds accordingly, and reconciles the recorded
# request against its own actual bind (ACTIVE_BIND_HOST): a match
# marks the restart confirmed; a mismatch marks it failed at the
# verify step, in plain words, with the live state named. The
# Settings row reads all of it from the bridge that actually
# answers, so it never lies about which state is live, and a
# restart that never completes is reported by the dashboard's
# confirmation polling as a named failure — never a silent
# pending. While the public bind is active, any request from a
# NON-loopback address must carry the access code's acceptance
# cookie before anything beyond the gate page is served —
# dashboard and API alike. Loopback is never gated, so every
# internal caller that polls 127.0.0.1 (launchers, the shell,
# status probes) works unchanged in both modes. One code, stored
# in the config's public_server block; the cookie's value is a
# hash of the code, so regenerating the code invalidates every
# previously accepted client at once.
ACTIVE_BIND_HOST = "127.0.0.1"
PUBLIC_COOKIE = "navi_public"
PUBLIC_COOKIE_MAX_AGE = 31536000


def public_settings(cfg):
    ps = cfg.get("public_server") if isinstance(cfg, dict) else None
    if not isinstance(ps, dict):
        ps = {}
    restart = ps.get("restart") if isinstance(ps.get("restart"), dict) else {}
    return {
        "enabled": ps.get("enabled") is True,
        "access_code": str(ps.get("access_code") or "").strip(),
        "restart_status": str(restart.get("status") or "idle"),
        "restart_step": str(restart.get("step") or ""),
        "restart_message": str(restart.get("message") or ""),
    }


def set_public_restart(cfg, status, step, message):
    block = cfg.get("public_server") if isinstance(cfg.get("public_server"), dict) else {}
    block = dict(block)
    if "enabled" not in block:
        block["enabled"] = False
    block["restart"] = {"status": status, "step": step, "message": message}
    cfg["public_server"] = block
    save_config(cfg)


def schedule_bridge_restart():
    # Exit 75 after the response has had a moment to flush: the
    # launcher's supervisor relaunches the bridge on 75, and the
    # new process binds per the saved Local server choice. If no
    # supervisor is listening (a bridge started by hand from a
    # since-closed terminal), the process simply stops and the
    # dashboard's confirmation polling names that failure and tells
    # the operator to relaunch Apex — a sentence, not a mystery.
    def _go():
        time.sleep(0.6)
        os._exit(75)
    threading.Thread(target=_go, daemon=True).start()


def generate_access_code():
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(8))
    return raw[:4] + "-" + raw[4:]


def ensure_access_code(cfg):
    code = public_settings(cfg)["access_code"]
    if code:
        return code
    code = generate_access_code()
    block = cfg.get("public_server") if isinstance(cfg.get("public_server"), dict) else {}
    block = dict(block)
    block["access_code"] = code
    if "enabled" not in block:
        block["enabled"] = False
    cfg["public_server"] = block
    save_config(cfg)
    return code


def public_token(code):
    return hashlib.sha256(("navi-public:" + str(code)).encode()).hexdigest()


def lan_ipv4():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"


# --- WAN detection (build .76, #59) ---------------------------------
# The honest address model: a LAN address is never a public address.
# The bridge learns this home's public (WAN) address with a small
# HTTPS echo lookup - the same class of outbound call the update
# check already makes - cached for five minutes, failure-tolerant:
# any failure degrades to "undetected" and never blocks an enable.
# APEX_DHD_WAN_IP is a diagnostics/test override only; unset in
# normal operation.
WAN_CACHE = {"ip": "", "state": "undetected", "at": 0.0}
WAN_ECHO_URLS = ("https://api.ipify.org", "https://checkip.amazonaws.com", "https://icanhazip.com")


def _ip_is_private_or_cgnat(ip):
    try:
        addr = ipaddress.ip_address(str(ip or "").strip())
    except Exception:
        return True
    if not isinstance(addr, ipaddress.IPv4Address):
        return True
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
        return True
    try:
        if addr in ipaddress.ip_network("100.64.0.0/10"):
            return True
    except Exception:
        pass
    return False


def wan_ipv4(force=False):
    # Returns (ip, state): state is "public" (a routable address was
    # seen), "behind-nat" (the echo answered with an RFC1918 or CGNAT
    # 100.64.0.0/10 address - this machine sits behind another router
    # or carrier NAT), or "undetected" (no echo answered).
    now = time.time()
    if not force and WAN_CACHE["at"] and (now - WAN_CACHE["at"] < 300):
        return WAN_CACHE["ip"], WAN_CACHE["state"]
    override = str(os.environ.get("APEX_DHD_WAN_IP", "")).strip()
    found = ""
    if override:
        try:
            ipaddress.IPv4Address(override)
            found = override
        except Exception:
            found = ""
    else:
        for url in WAN_ECHO_URLS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Apex-DHD"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    text = resp.read().decode("utf-8", "replace").strip()
                cand = text.split()[0].strip() if text.split() else ""
                ipaddress.IPv4Address(cand)
                found = cand
                break
            except Exception:
                continue
    if not found:
        ip, state = "", "undetected"
    elif _ip_is_private_or_cgnat(found):
        ip, state = found, "behind-nat"
    else:
        ip, state = found, "public"
    WAN_CACHE["ip"], WAN_CACHE["state"], WAN_CACHE["at"] = ip, state, now
    return ip, state


def public_state_payload(cfg, for_loopback):
    ps = public_settings(cfg)
    active_public = ACTIVE_BIND_HOST == "0.0.0.0"
    ip = lan_ipv4()
    return {
        "enabled": ps["enabled"],
        "activePublic": active_public,
        "bindHost": ACTIVE_BIND_HOST,
        "pending": ps["enabled"] != active_public,
        "lanIp": ip,
        "lanUrl": "http://" + ip + ":" + str(BRIDGE_PORT),
        "accessCode": ps["access_code"] if for_loopback else None,
        "restart": {
            "status": ps["restart_status"],
            "step": ps["restart_step"],
            "message": ps["restart_message"],
        },
    }


def _gate_escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _gate_stars_svg():
    # A fine starfield: 42 points placed by a fixed arithmetic
    # scatter, so the page is identical on every serve and carries
    # no external asset.
    dots = ""
    for i in range(42):
        x = (i * 97 + 31) % 400
        y = (i * 57 + 13) % 400
        r = "1.5" if i % 7 == 0 else "1"
        o = "0.9" if i % 5 == 0 else "0.5"
        dots += "<circle cx='" + str(x) + "' cy='" + str(y) + "' r='" + r + "' opacity='" + o + "'/>"
    return (
        "<svg class='stars' viewBox='0 0 400 400' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>"
        + dots
        + "</svg>"
    )


def _gate_ring_svg():
    # The DHD dial glyph as the page centerpiece: twelve chevron
    # wedges around a glowing core, drawn once as inline SVG (the
    # same glyph family as the app's DHD icon - outer ring, twelve
    # wedges, one warm center).
    wedges = ""
    for i in range(12):
        wedges += (
            "<g transform='rotate(" + str(i * 30) + " 100 100)'>"
            "<path class='chev' d='M100 12 L117 36 L100 28 L83 36 Z'/></g>"
        )
    return (
        "<svg class='ring' viewBox='0 0 200 200' role='img' aria-label='Apex dial ring'>"
        "<circle class='ring-track' cx='100' cy='100' r='88'/>"
        "<circle class='ring-track2' cx='100' cy='100' r='62'/>"
        + wedges
        + "<circle class='core-glow' cx='100' cy='100' r='34'/>"
        "<circle class='core' cx='100' cy='100' r='24'/>"
        "</svg>"
    )


_GATE_CSS = (
    "*{box-sizing:border-box}"
    "html,body{margin:0;padding:0}"
    "body{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "background-color:#04060d;color:#e6f1f5;min-height:100dvh;display:flex;"
    "align-items:center;justify-content:center;padding:20px 16px;position:relative;overflow-x:hidden;"
    "background-image:radial-gradient(900px 600px at 15% 10%,rgba(34,211,238,.16),transparent 60%),"
    "radial-gradient(800px 600px at 85% 90%,rgba(244,113,181,.12),transparent 60%),"
    "radial-gradient(600px 400px at 50% 45%,rgba(56,89,199,.10),transparent 65%)}"
    ".stars{position:fixed;inset:0;width:100%;height:100%;fill:#cfe9ff;pointer-events:none}"
    ".card{position:relative;width:100%;max-width:400px;background:rgba(11,17,26,.94);"
    "border:1px solid rgba(34,211,238,.38);border-radius:14px;padding:26px 24px 20px;"
    "box-shadow:0 24px 60px rgba(0,0,0,.55),0 0 32px rgba(34,211,238,.12)}"
    "@supports (backdrop-filter:blur(1px)){.card{background:rgba(11,17,26,.66);"
    "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}}"
    ".ring-wrap{width:min(190px,52vw);margin:2px auto 4px}"
    ".ring{width:100%;height:auto;display:block;overflow:visible;transform-origin:50% 50%}"
    ".ring-track{fill:none;stroke:rgba(34,211,238,.35);stroke-width:1.5}"
    ".ring-track2{fill:none;stroke:rgba(34,211,238,.18);stroke-width:1}"
    ".chev{fill:rgba(34,211,238,.75)}"
    ".core{fill:#f4502a}"
    ".core-glow{fill:rgba(244,80,42,.35);transform-box:fill-box;transform-origin:center}"
    ".door-dhd .ring{animation:gate-spin 140s linear infinite}"
    ".door-dhd .core-glow{animation:gate-pulse 3.4s ease-in-out infinite}"
    ".door-node .ring-wrap{opacity:.62}"
    ".door-node .core-glow{animation:gate-pulse 6s ease-in-out infinite}"
    "@keyframes gate-spin{to{transform:rotate(360deg)}}"
    "@keyframes gate-pulse{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(1.28);opacity:.95}}"
    ".shake{animation:gate-shake .45s ease}"
    "@keyframes gate-shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}"
    "40%{transform:translateX(6px)}60%{transform:translateX(-4px)}80%{transform:translateX(3px)}}"
    ".word{margin:10px 0 0;text-align:center;font-size:34px;font-weight:700;letter-spacing:.42em;padding-left:.42em}"
    ".powered{margin:5px 0 0;text-align:center;font-size:11px;letter-spacing:.22em;color:#9fb3c8;text-transform:uppercase}"
    ".doorline{margin:14px 0 0;text-align:center;font-size:13px;line-height:1.5;color:#9fb3c8}"
    ".knock{margin:3px 0 0;text-align:center;font-size:13px;color:#22d3ee;word-break:break-all}"
    ".hint{margin:8px 0 0;text-align:center;font-size:12px;line-height:1.55;color:#9fb3c8}"
    "form{margin-top:16px}"
    "label{display:block;font-size:11px;letter-spacing:.2em;color:#9fb3c8;text-transform:uppercase}"
    "input{width:100%;margin-top:7px;padding:14px 12px;min-height:54px;font:inherit;font-size:18px;"
    "letter-spacing:.3em;text-align:center;text-transform:uppercase;background:rgba(3,6,11,.85);"
    "color:#e6f1f5;border:1px solid #22303d;border-radius:8px}"
    "input:focus{outline:none;border-color:#22d3ee;box-shadow:0 0 0 3px rgba(34,211,238,.28),0 0 20px rgba(34,211,238,.30)}"
    "input:disabled{opacity:.45}"
    "button{width:100%;margin-top:12px;padding:14px;min-height:54px;font:inherit;font-size:16px;font-weight:700;"
    "color:#08131c;background:linear-gradient(120deg,#22d3ee,#f471b5);border:0;border-radius:8px;cursor:pointer}"
    "button:disabled{opacity:.45;cursor:default}"
    ".err{margin:14px 0 0;padding:10px 12px;font-size:13px;line-height:1.5;text-align:center;color:#fca5a5;"
    "background:rgba(248,113,113,.09);border:1px solid rgba(248,113,113,.4);border-radius:8px}"
    ".meta{margin:10px 0 0;text-align:center;font-size:12px;color:#f5b544}"
    "@media (max-width:380px){.card{padding:22px 16px 18px}.word{font-size:29px}}"
    "@media (prefers-reduced-motion:reduce){.door-dhd .ring,.door-dhd .core-glow,"
    ".door-node .core-glow,.shake{animation:none}}"
)


def gate_page_html(error="", door="node", name="", attempts_remaining=None, lock_seconds=None):
    # ONE gate page for both doors (build .79, issue #64): the Apex
    # Node (LAN) door and the DHD (public) door render from this
    # single function, parameterized by door - there is no second
    # copy. Self-contained by design: inline CSS and SVG only, no
    # external asset, font, or script referenced, because the gate
    # serves nothing else before the code. No version string
    # appears anywhere on the page. The form contract is unchanged:
    # POST /__gate with the field named "code".
    is_dhd = door == "dhd"
    if not name:
        if is_dhd:
            try:
                name = dhd_settings(load_config())["domain"]
            except Exception:
                name = ""
        else:
            try:
                name = socket.gethostname()
            except Exception:
                name = ""
    door_line = (
        "Dial-Home Device · you reached this Apex from the internet"
        if is_dhd
        else "Apex Node · on this network"
    )
    locked = lock_seconds is not None
    err_html = ""
    if error:
        err_html = "<p class='err' role='alert'>" + _gate_escape(error) + "</p>"
    meta_html = ""
    if locked:
        mins = max(1, int((int(lock_seconds) + 59) // 60))
        meta_html = (
            "<p class='meta'>This door is locked - try again in about "
            + str(mins)
            + " minute"
            + ("" if mins == 1 else "s")
            + ".</p>"
        )
    elif attempts_remaining is not None:
        n = int(attempts_remaining)
        meta_html = (
            "<p class='meta'>"
            + str(n)
            + " attempt"
            + ("" if n == 1 else "s")
            + " remaining before this door locks.</p>"
        )
    dis = " disabled" if locked else ""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Apex - access code</title><style>"
        + _GATE_CSS
        + "</style></head>"
        "<body class='"
        + ("door-dhd" if is_dhd else "door-node")
        + "'>"
        + _gate_stars_svg()
        + "<main class='"
        + ("card shake" if error else "card")
        + "'>"
        "<div class='ring-wrap'>"
        + _gate_ring_svg()
        + "</div>"
        "<h1 class='word'>APEX</h1>"
        "<p class='powered'>Powered by Navi</p>"
        "<p class='doorline'>"
        + door_line
        + "</p>"
        + ("<p class='knock'>" + _gate_escape(name) + "</p>" if name else "")
        + "<p class='hint'>Type the access code - you will find it on the DHD page, on the machine Apex runs on.</p>"
        + err_html
        + "<form method='POST' action='/__gate'>"
        "<label for='gate-code'>Access code</label>"
        "<input id='gate-code' name='code' autocomplete='one-time-code' autocapitalize='characters' autofocus"
        + dis
        + ">"
        "<button type='submit'"
        + dis
        + ">"
        + ("Locked" if locked else "Open Apex")
        + "</button>"
        "</form>"
        + meta_html
        + "</main></body></html>"
    )


# --- DHD (build .74) ------------------------------------------------
# DHD — Dial-Home Device, the way home: the SAME dashboard, extended
# to a genuinely public address on the operator's own machine.
# Everything is Apex's own work: no Tailscale, no external tunnel or
# proxy service, no Certbot. PROXY CHOICE (recorded in the build
# log, as directed): the smallest dependable approach this codebase
# supports is a reverse proxy inside this bridge process — Python
# standard library only. Two threaded listeners: port 80 serves the
# ACME HTTP-01 challenge path and redirects everything else to
# HTTPS; port 443 terminates TLS and forwards to the bridge on
# 127.0.0.1:8675. No new daemon, no nginx/caddy to install, and the
# openssl the installer already requires covers certificate work.
# The proxy is the ONLY public face: while DHD is enabled the
# bridge binds loopback only (main() enforces it), even when the
# Local server choice is on. There is no hand-edited proxy config:
# the proxy's behavior is derived from the config's dhd block on
# every start. TLS from the first click: no domain — Apex generates
# a self-signed certificate into config/dhd/; a domain — Apex's own
# ACME v2 client (below) obtains a real Let's Encrypt certificate
# and renews it automatically (checked at bridge start and daily;
# renewed at 30 days remaining or less). The gate rides the proxy:
# the SAME access code and acceptance cookie as the Local server,
# required before ANY dashboard or API content is served through
# the proxy — and public mode adds throttling the LAN door does not
# have: a progressive delay per wrong code and a temporary lockout
# after repeated failures. A passcode-authenticated session through
# the proxy is a full session: the proxy forwards the whole API,
# the Updater included — remote origin excludes nothing.
DHD_DIR = os.path.join(ROOT, "config", "dhd")
DHD_CERT_PATH = os.path.join(DHD_DIR, "cert.pem")
DHD_KEY_PATH = os.path.join(DHD_DIR, "key.pem")
DHD_META_PATH = os.path.join(DHD_DIR, "cert-meta.json")
DHD_CHALLENGE_DIR = os.path.join(DHD_DIR, "acme-challenge")
DHD_ACCOUNT_KEY = os.path.join(DHD_DIR, "acme-account.key")
DHD_STATE = {"running": False, "starting": False, "mode": "off", "last_error": ""}
DHD_SERVERS = []
DHD_THROTTLE = {}
DHD_LOCK = threading.Lock()
DHD_LOCKOUT_FAILS = 5
DHD_LOCKOUT_SECONDS = 300


def dhd_settings(cfg):
    d = cfg.get("dhd") if isinstance(cfg, dict) else None
    if not isinstance(d, dict):
        d = {}
    return {
        "enabled": d.get("enabled") is True,
        "domain": str(d.get("domain") or "").strip().lower(),
        "acme_directory": str(d.get("acme_directory") or "https://acme-v02.api.letsencrypt.org/directory").strip(),
    }


def dhd_save(cfg, patch):
    block = cfg.get("dhd") if isinstance(cfg.get("dhd"), dict) else {}
    block = dict(block)
    block.update(patch)
    cfg["dhd"] = block
    save_config(cfg)


def dhd_cert_meta():
    try:
        with open(DHD_META_PATH) as f:
            m = json.load(f)
        return m if isinstance(m, dict) else {}
    except Exception:
        return {}


def dhd_write_meta(mode, domain):
    os.makedirs(DHD_DIR, exist_ok=True)
    with open(DHD_META_PATH, "w") as f:
        json.dump({"mode": mode, "domain": domain}, f)


def dhd_cert_expiry():
    # The certificate's notAfter, read with openssl; (iso, days) or
    # (None, None). The meta file says which kind of cert it is;
    # openssl is the authority on when it ends.
    if not os.path.exists(DHD_CERT_PATH):
        return None, None
    try:
        out = subprocess.run(
            ["openssl", "x509", "-in", DHD_CERT_PATH, "-noout", "-enddate"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        raw = out.split("=", 1)[1].strip()
        dt = datetime.datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
        days = max(0, int((dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds() // 86400))
        return dt.isoformat(), days
    except Exception:
        return None, None


def dhd_generate_self_signed(domain=""):
    os.makedirs(DHD_DIR, exist_ok=True)
    sans = ["DNS:localhost", "IP:127.0.0.1"]
    if domain:
        sans.append("DNS:" + domain)
    try:
        ip = lan_ipv4()
        if ip and ip != "127.0.0.1":
            sans.append("IP:" + ip)
    except Exception:
        pass
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", DHD_KEY_PATH, "-out", DHD_CERT_PATH,
        "-days", "365", "-nodes", "-subj", "/CN=Apex DHD",
        "-addext", "subjectAltName=" + ",".join(sans),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("openssl could not generate the self-signed certificate: " + (r.stderr or "").strip()[:200])
    dhd_write_meta("self-signed", domain)


def dhd_ensure_server_key():
    if os.path.exists(DHD_KEY_PATH):
        return
    os.makedirs(DHD_DIR, exist_ok=True)
    r = subprocess.run(["openssl", "genrsa", "-out", DHD_KEY_PATH, "2048"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("openssl could not generate the server key: " + (r.stderr or "").strip()[:200])


# -- The built-in ACME v2 client -------------------------------------
# Account key, order, HTTP-01 challenge served through the Apex
# proxy on port 80, finalize, download, install. JWS signing shells
# to openssl (RS256); HTTP is urllib. The directory URL comes from
# the config's dhd block, so the client can be pointed at Let's
# Encrypt staging or a local stub directory unchanged.

def _b64u(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _acme_http(method, url, body=None, ctype=None):
    req = urllib.request.Request(url, data=body, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
    req.add_header("User-Agent", "apex-dhd-acme")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def _der_read_len(buf, i):
    b = buf[i]
    i += 1
    if b < 0x80:
        return b, i
    n = b & 0x7F
    v = 0
    for _ in range(n):
        v = (v << 8) | buf[i]
        i += 1
    return v, i


def _der_read_tlv(buf, i):
    tag = buf[i]
    i += 1
    ln, i = _der_read_len(buf, i)
    return tag, buf[i:i + ln], i + ln


def _rsa_jwk_from_private_key(key_path):
    # The account key's JWK (for the thumbprint): pull the public
    # numbers out of the SubjectPublicKeyInfo DER with a minimal
    # ASN.1 walk — modulus and exponent are all a thumbprint needs.
    r = subprocess.run(["openssl", "rsa", "-in", key_path, "-pubout", "-outform", "DER"], capture_output=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("openssl could not read the ACME account key")
    buf = r.stdout
    _t, spki, _e = _der_read_tlv(buf, 0)
    i = 0
    _t, _alg, i = _der_read_tlv(spki, i)
    _t, bits, i = _der_read_tlv(spki, i)
    _t, rsaseq, _e = _der_read_tlv(bits[1:], 0)
    j = 0
    _t, n_bytes, j = _der_read_tlv(rsaseq, j)
    _t, e_bytes, j = _der_read_tlv(rsaseq, j)
    strip = lambda b: b[1:] if len(b) > 1 and b[0] == 0 else b
    return {"e": _b64u(strip(e_bytes)), "kty": "RSA", "n": _b64u(strip(n_bytes))}


def _acme_jws(key_path, url, payload, nonce, kid=None, jwk=None):
    protected = {"alg": "RS256", "nonce": nonce, "url": url}
    if kid:
        protected["kid"] = kid
    else:
        protected["jwk"] = jwk
    p64 = _b64u(json.dumps(protected, separators=(",", ":")))
    body = "" if payload is None else json.dumps(payload, separators=(",", ":"))
    b64 = _b64u(body)
    signing = (p64 + "." + b64).encode()
    fd, tmp = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(signing)
        r = subprocess.run(["openssl", "dgst", "-sha256", "-sign", key_path, tmp], capture_output=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError("openssl could not sign the ACME request")
        sig = r.stdout
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass
    return json.dumps({"protected": p64, "payload": b64, "signature": _b64u(sig)}, separators=(",", ":")).encode()


def acme_obtain(domain, directory_url):
    # One full issuance for the domain. Raises RuntimeError with a
    # plain-words step name on failure; installs the certificate
    # and reloads the proxy on success.
    os.makedirs(DHD_CHALLENGE_DIR, exist_ok=True)
    if not os.path.exists(DHD_ACCOUNT_KEY):
        r = subprocess.run(["openssl", "genrsa", "-out", DHD_ACCOUNT_KEY, "2048"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError("ACME step 'account key' failed: openssl could not generate the account key")
    jwk = _rsa_jwk_from_private_key(DHD_ACCOUNT_KEY)
    thumb = _b64u(hashlib.sha256(json.dumps(
        {"e": jwk["e"], "kty": "RSA", "n": jwk["n"]}, separators=(",", ":"), sort_keys=True,
    ).encode()).digest())
    _s, _h, raw = _acme_http("GET", directory_url)
    try:
        directory = json.loads(raw.decode())
        new_nonce_url = directory["newNonce"]
        new_account_url = directory["newAccount"]
        new_order_url = directory["newOrder"]
    except Exception:
        raise RuntimeError("ACME step 'directory' failed: the ACME directory did not answer as expected at " + directory_url)
    state = {"nonce": ""}

    def fresh_nonce():
        _s, h, _b = _acme_http("HEAD", new_nonce_url)
        state["nonce"] = h.get("Replay-Nonce", "")

    def post(url, payload, kid=None, use_jwk=False):
        fresh_nonce()
        body = _acme_jws(DHD_ACCOUNT_KEY, url, payload, state["nonce"], kid=kid, jwk=(jwk if use_jwk else None))
        status, headers, raw = _acme_http("POST", url, body=body, ctype="application/jose+json")
        if headers.get("Replay-Nonce"):
            state["nonce"] = headers["Replay-Nonce"]
        data = None
        try:
            data = json.loads(raw.decode()) if raw else None
        except Exception:
            data = None
        return status, headers, data, raw

    status, headers, _d, _r = post(new_account_url, {"termsOfServiceAgreed": True}, use_jwk=True)
    account_url = headers.get("Location", "")
    if status not in (200, 201) or not account_url:
        raise RuntimeError("ACME step 'account' failed: the ACME server refused the account (HTTP " + str(status) + ")")
    status, order_headers, order, _r = post(new_order_url, {"identifiers": [{"type": "dns", "value": domain}]}, kid=account_url)
    if status not in (200, 201) or not isinstance(order, dict):
        raise RuntimeError("ACME step 'order' failed: the ACME server refused the order (HTTP " + str(status) + ")")
    order_url = order_headers.get("Location", "")
    authz_urls = order.get("authorizations") or []
    finalize_url = order.get("finalize", "")
    if not authz_urls or not finalize_url:
        raise RuntimeError("ACME step 'order' failed: the order carried no authorization")
    status, _h, authz, _r = post(authz_urls[0], None, kid=account_url)
    if not isinstance(authz, dict):
        raise RuntimeError("ACME step 'challenge' failed: the authorization did not load")
    challenge = None
    for c in authz.get("challenges") or []:
        if c.get("type") == "http-01":
            challenge = c
            break
    if not challenge:
        raise RuntimeError("ACME step 'challenge' failed: no HTTP-01 challenge was offered")
    token = str(challenge.get("token") or "")
    key_auth = token + "." + thumb
    with open(os.path.join(DHD_CHALLENGE_DIR, token), "w") as f:
        f.write(key_auth)
    status, _h, _d, _r = post(str(challenge.get("url") or ""), {}, kid=account_url)
    if status not in (200, 201):
        raise RuntimeError("ACME step 'challenge' failed: the ACME server refused the challenge response (HTTP " + str(status) + ")")
    valid = False
    for _ in range(30):
        time.sleep(1)
        _s, _h, a2, _r = post(authz_urls[0], None, kid=account_url)
        if isinstance(a2, dict) and a2.get("status") == "valid":
            valid = True
            break
        if isinstance(a2, dict) and a2.get("status") == "invalid":
            break
    if not valid:
        raise RuntimeError("ACME step 'challenge' failed: the domain proof did not validate — the usual cause is port 80 not reaching this machine (check the router forward) or the domain not resolving here yet")
    dhd_ensure_server_key()
    fd, csr_path = tempfile.mkstemp()
    os.close(fd)
    try:
        r = subprocess.run(
            ["openssl", "req", "-new", "-key", DHD_KEY_PATH, "-subj", "/CN=" + domain,
             "-addext", "subjectAltName=DNS:" + domain, "-outform", "DER", "-out", csr_path],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            raise RuntimeError("ACME step 'finalize' failed: openssl could not build the certificate request")
        with open(csr_path, "rb") as f:
            csr_b64 = _b64u(f.read())
    finally:
        try:
            os.unlink(csr_path)
        except Exception:
            pass
    status, _h, order2, _r = post(finalize_url, {"csr": csr_b64}, kid=account_url)
    if status not in (200, 201) or not isinstance(order2, dict):
        raise RuntimeError("ACME step 'finalize' failed: the ACME server refused the finalize (HTTP " + str(status) + ")")
    cert_url = order2.get("certificate", "")
    for _ in range(30):
        if cert_url:
            break
        if not order_url:
            break
        time.sleep(1)
        _s, _h, o3, _r = post(order_url, None, kid=account_url)
        if isinstance(o3, dict):
            cert_url = o3.get("certificate", "") or cert_url
            if o3.get("status") == "invalid":
                break
    if not cert_url:
        raise RuntimeError("ACME step 'download' failed: the order never produced a certificate")
    status, _h, _d, raw = post(cert_url, None, kid=account_url)
    if status != 200 or b"BEGIN CERTIFICATE" not in raw:
        raise RuntimeError("ACME step 'download' failed: the certificate did not download (HTTP " + str(status) + ")")
    os.makedirs(DHD_DIR, exist_ok=True)
    with open(DHD_CERT_PATH, "wb") as f:
        f.write(raw)
    dhd_write_meta("domain", domain)
    return True


# -- The proxy itself --------------------------------------------------

def dhd_gate_page(handler):
    # The DHD door's gate page, rendered through the ONE shared
    # renderer with the door's throttle state surfaced: attempts
    # remaining before lockout, and - while locked - the form
    # disabled with the remaining lockout time. The throttle itself
    # is unchanged; this only shows what it already knows.
    ip = handler._client_ip()
    fails, lock_until = dhd_throttle_state(ip)
    host = handler.headers.get("Host") or ""
    if lock_until > time.time():
        return gate_page_html(
            "Too many wrong codes - this door is locked.",
            door="dhd",
            name=host,
            lock_seconds=int(lock_until - time.time()),
        )
    if fails > 0:
        return gate_page_html(
            "",
            door="dhd",
            name=host,
            attempts_remaining=max(0, DHD_LOCKOUT_FAILS - fails),
        )
    return gate_page_html("", door="dhd", name=host)


def dhd_throttle_state(ip):
    with DHD_LOCK:
        st = DHD_THROTTLE.get(ip)
        if not st:
            return 0, 0.0
        return st.get("fails", 0), st.get("lock_until", 0.0)


def dhd_throttle_fail(ip):
    with DHD_LOCK:
        st = DHD_THROTTLE.setdefault(ip, {"fails": 0, "lock_until": 0.0})
        st["fails"] = st.get("fails", 0) + 1
        fails = st["fails"]
        if fails >= DHD_LOCKOUT_FAILS:
            st["lock_until"] = time.time() + DHD_LOCKOUT_SECONDS
        return fails


def dhd_throttle_clear(ip):
    with DHD_LOCK:
        DHD_THROTTLE.pop(ip, None)


class DhdProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ApexDHD"

    def log_message(self, fmt, *args):
        pass

    def _send_raw(self, code, body, ctype="text/html; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Exactly ONE no-store header (build .91): a forwarded
        # response arrives with the bridge's own Cache-Control in
        # extra, and sending this one too put the pair on the wire.
        _extra_has_cc = bool(extra) and any(str(k).lower() == "cache-control" for k in extra)
        if not _extra_has_cc:
            self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except Exception:
                pass

    def _client_ip(self):
        try:
            return str(self.client_address[0] or "")
        except Exception:
            return ""

    def _accepted(self):
        code = public_settings(load_config())["access_code"]
        if not code:
            return False
        want = PUBLIC_COOKIE + "=" + public_token(code)
        parts = [p.strip() for p in (self.headers.get("Cookie") or "").split(";")]
        return want in parts

    def _serve_challenge(self, path):
        token = path.rsplit("/", 1)[-1]
        if not token or "/" in token or ".." in token:
            self._send_raw(404, "not found", "text/plain")
            return
        fp = os.path.join(DHD_CHALLENGE_DIR, token)
        try:
            with open(fp) as f:
                body = f.read()
            self._send_raw(200, body, "text/plain")
        except Exception:
            self._send_raw(404, "not found", "text/plain")

    def _forward(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else None
        headers = {}
        for k, v in self.headers.items():
            lk = k.lower()
            if lk in ("host", "connection", "content-length", "keep-alive", "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade"):
                continue
            headers[k] = v
        headers["Host"] = "127.0.0.1:" + str(BRIDGE_PORT)
        headers["X-Forwarded-For"] = self._client_ip()
        headers["X-Forwarded-Proto"] = "https"
        headers["X-Apex-Via"] = "dhd"
        conn = http.client.HTTPConnection("127.0.0.1", BRIDGE_PORT, timeout=60)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
            out_headers = {}
            for k, v in resp.getheaders():
                lk = k.lower()
                if lk in ("connection", "content-length", "keep-alive", "transfer-encoding"):
                    continue
                out_headers[k] = v
            self._send_raw(resp.status, data, resp.getheader("Content-Type") or "application/octet-stream", extra=out_headers)
        except Exception:
            self._send_raw(502, "Apex is not answering behind the DHD door right now.", "text/plain")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _gate_post(self):
        ip = self._client_ip()
        _fails, lock_until = dhd_throttle_state(ip)
        if lock_until > time.time():
            wait = int(lock_until - time.time())
            self._send_raw(429, gate_page_html("Too many wrong codes - this door is locked.", door="dhd", name=self.headers.get("Host") or "", lock_seconds=wait))
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            form = urllib.parse.parse_qs(raw.decode("utf-8", "replace"))
            given = (form.get("code") or [""])[0].strip()
        except Exception:
            given = ""
        want = public_settings(load_config())["access_code"]
        if want and given.upper() == want.upper():
            dhd_throttle_clear(ip)
            cookie = PUBLIC_COOKIE + "=" + public_token(want) + "; Max-Age=" + str(PUBLIC_COOKIE_MAX_AGE) + "; Path=/; HttpOnly; SameSite=Lax"
            self._send_raw(302, "", "text/plain", extra={"Location": "/", "Set-Cookie": cookie})
            return
        fails = dhd_throttle_fail(ip)
        if fails >= DHD_LOCKOUT_FAILS:
            self._send_raw(429, gate_page_html("Too many wrong codes - this door is now locked.", door="dhd", name=self.headers.get("Host") or "", lock_seconds=DHD_LOCKOUT_SECONDS))
            return
        # Progressive delay: each wrong code makes the next answer
        # slower (1s, 2s, 4s, capped at 8s).
        time.sleep(min(2 ** (fails - 1), 8))
        self._send_raw(200, gate_page_html("That code did not open the door.", door="dhd", name=self.headers.get("Host") or "", attempts_remaining=max(0, DHD_LOCKOUT_FAILS - fails)))

    def _handle(self):
        path = self.path.split("?")[0]
        is_tls = isinstance(self.connection, ssl.SSLSocket)
        if not is_tls:
            # Port 80: the ACME challenge path, and nothing else
            # but a redirect behind it.
            if path.startswith("/.well-known/acme-challenge/"):
                self._serve_challenge(path)
                return
            host = self.headers.get("Host") or ""
            target = "https://" + host + self.path if host else "/"
            self._send_raw(301, "", "text/plain", extra={"Location": target})
            return
        if path.startswith("/.well-known/acme-challenge/"):
            self._serve_challenge(path)
            return
        if path == "/__gate":
            if self.command == "POST":
                self._gate_post()
            else:
                self._send_raw(200, dhd_gate_page(self))
            return
        if path.startswith("/mesh/"):
            # Build .86: Mesh NEVER rides the DHD door. Mesh has
            # its own dedicated TLS listener (the mesh port, its
            # own certificate) in every configuration, so the
            # proxy refuses /mesh/* outright — it never serves it
            # and never forwards it to the dashboard.
            self._send_raw(403, json.dumps({"ok": False, "reason": "unauthorized"}), "application/json")
            return
        if not self._accepted():
            if path.startswith("/api/"):
                self._send_raw(403, json.dumps({"error": "access code required"}), "application/json")
            else:
                self._send_raw(200, dhd_gate_page(self))
            return
        self._forward()

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_DELETE = _handle
    do_PATCH = _handle
    do_HEAD = _handle


def dhd_start_proxy():
    # Brings both listeners up with the certificate on disk.
    # Raises RuntimeError naming the step on failure.
    global DHD_SERVERS
    dhd_stop_proxy()
    if not os.path.exists(DHD_CERT_PATH):
        raise RuntimeError("DHD could not start at the TLS step: no certificate is on disk")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ctx.load_cert_chain(DHD_CERT_PATH, DHD_KEY_PATH)
    except Exception as e:
        raise RuntimeError("DHD could not start at the TLS step: the certificate could not be loaded (" + str(e) + ")")
    try:
        http_server = ThreadingHTTPServer(("0.0.0.0", 80), DhdProxyHandler)
    except PermissionError:
        raise RuntimeError("DHD could not start at the proxy step: ports below 1024 are reserved on Linux - grant the bridge the low-port capability once (sudo setcap 'cap_net_bind_service=+ep' on the python3 binary), then flip the switch again")
    except OSError as e:
        raise RuntimeError("DHD could not start at the proxy step: port 80 is not free (" + str(e) + ") - something else on this machine is using it")
    try:
        https_server = ThreadingHTTPServer(("0.0.0.0", 443), DhdProxyHandler)
        https_server.socket = ctx.wrap_socket(https_server.socket, server_side=True)
    except PermissionError:
        try:
            http_server.server_close()
        except Exception:
            pass
        raise RuntimeError("DHD could not start at the proxy step: ports below 1024 are reserved on Linux - grant the bridge the low-port capability once (sudo setcap 'cap_net_bind_service=+ep' on the python3 binary), then flip the switch again")
    except OSError as e:
        try:
            http_server.server_close()
        except Exception:
            pass
        raise RuntimeError("DHD could not start at the proxy step: port 443 is not free (" + str(e) + ") - something else on this machine is using it")
    DHD_SERVERS = [http_server, https_server]
    for srv in DHD_SERVERS:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    DHD_STATE["running"] = True
    return True


def dhd_stop_proxy():
    global DHD_SERVERS
    for srv in DHD_SERVERS:
        try:
            srv.shutdown()
        except Exception:
            pass
        try:
            srv.server_close()
        except Exception:
            pass
    DHD_SERVERS = []
    DHD_STATE["running"] = False


def dhd_self_check():
    # After the proxy starts: it must answer on 443 from this
    # machine. The gate page answering IS the healthy answer for
    # an unauthenticated local probe.
    try:
        ctx = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection("127.0.0.1", 443, timeout=10, context=ctx)
        conn.request("GET", "/__gate")
        resp = conn.getresponse()
        resp.read()
        conn.close()
        return resp.status == 200
    except Exception:
        return False


def dhd_domain_resolves_here(domain):
    try:
        infos = socket.getaddrinfo(domain, 443, proto=socket.IPPROTO_TCP)
        ips = set()
        for info in infos:
            ips.add(str(info[4][0]))
        wan_ip, _wan_state = wan_ipv4()
        return lan_ipv4() in ips or "127.0.0.1" in ips or (bool(wan_ip) and wan_ip in ips)
    except Exception:
        return False


def dhd_bring_up(cfg, reason="enable", progress=None):
    # The one-click ladder, in order: certificate, proxy, check.
    # A failed step records its name and leaves the previous live
    # state untouched - a proxy already running keeps running. The
    # optional progress callback is the operation-card feed: the
    # same ladder, reported step by step, never a second path.
    ds = dhd_settings(cfg)
    domain = ds["domain"]
    stage = "certificate"
    DHD_STATE["starting"] = True

    def mark(step, state, detail="", commands=None):
        if progress:
            progress(step, state, detail, commands or [])

    try:
        mark("certificate", "running", "Preparing the certificate.")
        meta = dhd_cert_meta()
        _exp, days_left = dhd_cert_expiry()
        have_domain_cert = meta.get("mode") == "domain" and meta.get("domain") == domain and os.path.exists(DHD_CERT_PATH)
        if domain and not have_domain_cert:
            try:
                acme_obtain(domain, ds["acme_directory"])
            except Exception as e:
                # The door still opens today on a self-signed
                # certificate; the failure is named, not hidden.
                DHD_STATE["last_error"] = str(e)
                if not os.path.exists(DHD_CERT_PATH) or meta.get("mode") == "domain":
                    dhd_generate_self_signed(domain)
        elif domain and have_domain_cert and days_left is not None and days_left <= 30:
            try:
                acme_obtain(domain, ds["acme_directory"])
            except Exception as e:
                DHD_STATE["last_error"] = "Renewal attempt failed (the current certificate still has " + str(days_left) + " days): " + str(e)
        elif not domain:
            if not os.path.exists(DHD_CERT_PATH) or meta.get("mode") != "self-signed":
                dhd_generate_self_signed("")
        mark("certificate", "done", DHD_STATE["last_error"] if domain and not have_domain_cert else "Certificate ready.")
        stage = "proxy"
        mark("proxy", "running", "Starting Apex's reverse proxy on ports 80 and 443.")
        was_running = DHD_STATE["running"]
        if was_running and reason == "enable":
            # Re-enable with Apex's own proxy already listening is a
            # healthy state, never a port problem (#59): the door is
            # already working, so there is nothing to restart.
            mark("proxy", "done", "Apex's DHD proxy is already listening on 80/443 - this door working.")
        else:
            try:
                dhd_start_proxy()
            except Exception:
                if was_running:
                    # Reload failed; try to restore the previous face.
                    try:
                        dhd_start_proxy()
                    except Exception:
                        pass
                raise
            mark("proxy", "done", "The proxy is listening and forwarding to the bridge on loopback.")
        stage = "reachability"
        mark("reachability", "running", "Local check: confirming the proxy answers on 443 from this machine (answered on this machine proves the local half only - outside reach is reported separately).")
        meta = dhd_cert_meta()
        DHD_STATE["mode"] = meta.get("mode", "self-signed")
        if not dhd_self_check():
            raise RuntimeError("DHD started, but the reachability self-check failed: the proxy did not answer on 443 from this machine")
        if domain and DHD_STATE["mode"] != "domain":
            # Certificate pending is a degraded state, named here
            # so the page and the Servers dot can show it.
            if not DHD_STATE["last_error"]:
                DHD_STATE["last_error"] = "Domain saved - its certificate is still pending."
        elif DHD_STATE["mode"] == "domain":
            DHD_STATE["last_error"] = ""
        return True
    except Exception as e:
        DHD_STATE["last_error"] = str(e)
        mark(stage, "failed", str(e), dhd_failure_commands(stage, str(e), domain))
        return False
    finally:
        DHD_STATE["starting"] = False


def _dhd_on_summary(payload):
    # One honest sentence about a live DHD, shared by the operation
    # cards, the chat replies, and the bridge's own startup line.
    mode = payload.get("mode", "self-signed")
    if payload.get("publicVerified"):
        return "DHD is on at " + payload["publicUrl"] + " (" + mode + ") - outside reach verified."
    if payload.get("publicUrl"):
        return "DHD is on (" + mode + "). On this network: " + (payload.get("lanUrl") or "this machine") + ". Public address " + payload["publicUrl"] + " - outside reach unverified: " + (payload.get("nextStep") or "")
    return "DHD is on (" + mode + "). On this network: " + (payload.get("lanUrl") or "this machine") + ". No public address yet - outside reach unverified: " + (payload.get("nextStep") or "")


def dhd_state_payload(cfg, for_loopback):
    ds = dhd_settings(cfg)
    meta = dhd_cert_meta()
    expires, days_left = dhd_cert_expiry()
    active = bool(DHD_STATE["running"])
    mode = "off" if not ds["enabled"] else (meta.get("mode", "self-signed") if active else "off")
    cert_pending = bool(ds["domain"]) and mode != "domain"
    if not ds["enabled"]:
        status = "off"
    elif DHD_STATE["starting"]:
        status = "starting"
    elif not active:
        status = "degraded"
    elif cert_pending:
        status = "degraded"
    else:
        status = "healthy"
    # The honest address model (build .76, #59). Three different
    # addresses, never conflated: the LAN address (this network
    # only), the detected WAN address (this home's public IP, seen
    # by an outside echo - shown, but outside reach stays
    # UNVERIFIED until it is proven), and the domain (the public
    # address once its certificate is live AND the name resolves
    # to this machine - only then is outside reach verified).
    lan_ip = lan_ipv4()
    lan_url = ("https://" + lan_ip) if (ds["enabled"] and active) else ""
    wan_ip, wan_state = "", "undetected"
    if ds["enabled"] and active:
        wan_ip, wan_state = wan_ipv4()
    domain_live = bool(ds["domain"]) and mode == "domain"
    resolves_here = dhd_domain_resolves_here(ds["domain"]) if domain_live else False
    public_verified = bool(domain_live and resolves_here)
    public_url = ""
    if ds["enabled"] and active:
        if public_verified:
            public_url = "https://" + ds["domain"]
        elif wan_state == "public" and wan_ip:
            public_url = "https://" + wan_ip
    if public_verified:
        outside_reach = "verified"
        next_step = ""
        wan_note = ""
    elif not (ds["enabled"] and active):
        outside_reach = "none"
        next_step = ""
        wan_note = ""
    else:
        outside_reach = "unverified"
        if wan_state == "behind-nat":
            wan_note = "The address the internet sees for this home (" + wan_ip + ") is itself a private or carrier-NAT address - this machine sits behind another router/NAT, so it is not directly reachable from outside."
            next_step = "Forward ports 443 and 80 on the outer router to this machine, or add your domain - outside reach stays unverified until the public path is proven."
        elif wan_state == "undetected":
            wan_note = "Apex could not detect this home's public address (the echo lookup did not answer)."
            next_step = "Forward ports 443 and 80 on your router to this machine, or add your domain - outside reach stays unverified until the public path is proven."
        else:
            wan_note = ""
            next_step = "Forward ports 443 and 80 on your router to this machine (" + lan_ip + "), or add your domain - outside reach stays unverified until the public path is proven."
    return {
        "enabled": ds["enabled"],
        "active": active,
        "domain": ds["domain"],
        "mode": mode,
        "status": status,
        "publicUrl": public_url,
        "lanIp": lan_ip,
        "lanUrl": lan_url,
        "wanIp": wan_ip,
        "wanState": wan_state,
        "wanNote": wan_note,
        "publicVerified": public_verified,
        "outsideReach": outside_reach,
        "nextStep": next_step,
        "domainResolvesHere": resolves_here,
        "certExpiresAt": expires,
        "certDaysLeft": days_left,
        "certPending": cert_pending and ds["enabled"],
        "lastError": DHD_STATE["last_error"],
        "accessCode": public_settings(cfg)["access_code"] if for_loopback else None,
        "prereqs": dhd_prereq_check(),
        "lastOperation": op_latest("dhd-enable"),
    }


def dhd_renewal_loop():
    # Renewal is automatic: checked when the bridge starts (this
    # thread's first pass) and daily after that. A domain cert at
    # 30 days remaining or less is renewed with no operator
    # action; a self-signed cert is regenerated the same way.
    while True:
        try:
            cfg = load_config()
            ds = dhd_settings(cfg)
            if ds["enabled"] and DHD_STATE["running"]:
                _exp, days_left = dhd_cert_expiry()
                if days_left is not None and days_left <= 30:
                    dhd_bring_up(cfg, reason="renewal")
        except Exception:
            pass
        time.sleep(86400)


# -- DHD prerequisites, remedies, and operation cards (build .74) --
# The installer lands DHD's prerequisites up front; this section is
# the safety net and the shared operation engine. A check names
# each missing piece, an install action uses the same distro-family
# package step as the installer, and every failure that has a
# manual remedy carries the exact copy-ready commands for this
# machine's family. Operations are deterministic bridge state: no
# model call is made while one runs, steps and outputs stay inline,
# and a finished operation is persisted so its card remains in the
# chat thread after the work ends. APEX_DHD_MISSING and
# APEX_DHD_INSTALL_FAIL are diagnostics/test overrides only; unset
# in normal operation.

OPS_PATH = os.path.join(ROOT, "config", "operations.json")
OPS = {}
OPS_LOADED = False
OPS_LOCK = threading.Lock()
OP_EVENTS = {}
OP_RESUME = {}


def _dhd_env_set(name):
    out = set()
    for part in str(os.environ.get(name, "")).split(","):
        part = part.strip().lower().replace("_", "-")
        if part:
            out.add(part)
    return out


DHD_SIM_MISSING = _dhd_env_set("APEX_DHD_MISSING")
DHD_SIM_INSTALL_FAIL = _dhd_env_set("APEX_DHD_INSTALL_FAIL")


def detect_distro_family():
    data = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k] = v.strip().strip('"')
    except Exception:
        pass
    distro_id = str(data.get("ID", "")).lower()
    like = str(data.get("ID_LIKE", "")).lower()
    label = str(data.get("PRETTY_NAME") or distro_id or "Unrecognized Linux")
    if distro_id == "bazzite":
        return "bazzite", label
    if distro_id in ("debian", "ubuntu", "pop", "linuxmint", "raspbian") or "debian" in like or "ubuntu" in like:
        return "debian", label
    if distro_id in ("fedora", "rhel", "centos") or "fedora" in like:
        return "fedora", label
    if distro_id in ("arch", "manjaro", "endeavouros") or "arch" in like:
        return "arch", label
    return "unknown", label


def _python3_path():
    p = shutil.which("python3") or sys.executable or "python3"
    try:
        return os.path.realpath(p)
    except Exception:
        return p


def dhd_lowport_commands():
    return ["sudo setcap 'cap_net_bind_service=+ep' " + chr(34) + _python3_path() + chr(34)]


def dhd_manual_commands(piece, family=None):
    if family is None:
        family, _label = detect_distro_family()
    if piece == "openssl":
        if family == "debian":
            return ["sudo apt-get update", "sudo apt-get install -y openssl"]
        if family == "fedora":
            return ["sudo dnf install -y openssl"]
        if family == "arch":
            return ["sudo pacman -S --needed openssl"]
        if family == "bazzite":
            return [
                "# Bazzite does not layer host packages; use its Fedora distrobox for the remedy:",
                "distrobox enter fedora -- sudo dnf install -y openssl",
            ]
        return [
            "# Install the openssl package with this distro's package manager, for example:",
            "sudo apt-get install -y openssl",
        ]
    if piece == "proxy":
        return [
            "# The DHD proxy is built into bridge.py; there is no separate proxy package to install.",
            "# Reinstall or update Apex so bridge.py is whole, then flip the DHD switch again.",
        ]
    if piece == "certhome":
        return [
            'sudo install -d -o "$USER" -g "$(id -gn)" "' + DHD_DIR + '"',
            'chmod -R u+rwX "' + DHD_DIR + '"',
        ]
    if piece == "lowport":
        return dhd_lowport_commands()
    if piece in ("port80", "port443"):
        port = "80" if piece == "port80" else "443"
        return [
            "sudo ss -ltnp 'sport = :" + port + "'",
            "# Stop the process named above (or move it to another port), then flip the DHD switch again.",
        ]
    return []


def dhd_failure_commands(stage, error, domain=""):
    text = str(error or "")
    low = text.lower()
    family, _label = detect_distro_family()
    if "cap_net_bind_service" in low or "ports below 1024" in low or "permission" in low and ("proxy step" in low or "port" in low):
        return dhd_lowport_commands()
    if "port 80 is not free" in low:
        return dhd_manual_commands("port80", family)
    if "port 443 is not free" in low:
        return dhd_manual_commands("port443", family)
    if "openssl" in low or "certificate" in low or "acme step" in low:
        return dhd_manual_commands("openssl", family)
    if stage == "reachability" and domain:
        return [
            'dig +short "' + domain + '"',
            'curl -I "http://' + domain + '/.well-known/acme-challenge/test"',
            "# The first command should return this machine's public IP; the second should reach Apex on port 80.",
        ]
    if stage == "proxy":
        return dhd_manual_commands("proxy", family)
    return []


def _dhd_port_state(port):
    if DHD_STATE.get("running"):
        return "ok", "In use by Apex's DHD proxy - this door working."
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind(("0.0.0.0", port))
        return "ok", "Port " + str(port) + " is free."
    except PermissionError:
        return "permission", "Port " + str(port) + " needs the low-port capability on this Linux setup."
    except OSError as e:
        return "busy", "Port " + str(port) + " is already in use (" + str(e) + ")."
    finally:
        try:
            sock.close()
        except Exception:
            pass


def dhd_prereq_check():
    family, label = detect_distro_family()
    out = []
    proxy_ok = "DhdProxyHandler" in globals() and hasattr(ssl, "SSLContext") and "proxy" not in DHD_SIM_MISSING
    out.append({
        "id": "proxy", "name": "Reverse proxy component", "ok": bool(proxy_ok),
        "detail": "Built into bridge.py and present." if proxy_ok else "The proxy component did not pass Apex's self-test.",
        "installable": True, "commands": dhd_manual_commands("proxy", family),
    })
    openssl_path = shutil.which("openssl")
    openssl_ok = bool(openssl_path) and "openssl" not in DHD_SIM_MISSING
    openssl_detail = "Not found on PATH."
    if openssl_path:
        try:
            v = subprocess.run([openssl_path, "version"], capture_output=True, text=True, timeout=10).stdout.strip()
            openssl_detail = (v or openssl_path) + " is present."
        except Exception:
            openssl_detail = openssl_path + " is present."
    if not openssl_ok and openssl_path:
        openssl_detail = "Apex's prerequisite check is holding openssl as missing (diagnostics override)."
    out.append({
        "id": "openssl", "name": "OpenSSL binary", "ok": bool(openssl_ok),
        "detail": openssl_detail,
        "installable": family in ("debian", "fedora", "arch"),
        "commands": dhd_manual_commands("openssl", family),
    })
    cert_ok = "certhome" not in DHD_SIM_MISSING and "cert-home" not in DHD_SIM_MISSING
    cert_detail = "Certificate home is writable: " + DHD_DIR
    if cert_ok:
        try:
            os.makedirs(DHD_DIR, exist_ok=True)
            probe = os.path.join(DHD_DIR, ".apex-write-test-" + str(os.getpid()) + "-" + str(threading.get_ident()) + "-" + str(time.time_ns()))
            with open(probe, "w") as f:
                f.write("ok")
            os.unlink(probe)
        except Exception as e:
            cert_ok = False
            cert_detail = "Certificate home is not writable: " + str(e)
    else:
        cert_detail = "Apex's prerequisite check is holding the certificate home as unavailable (diagnostics override)."
    out.append({
        "id": "certhome", "name": "Certificate home", "ok": bool(cert_ok),
        "detail": cert_detail, "installable": True,
        "commands": dhd_manual_commands("certhome", family),
    })
    for port, piece in ((80, "port80"), (443, "port443")):
        state, detail = _dhd_port_state(port)
        commands = dhd_lowport_commands() if state == "permission" else dhd_manual_commands(piece, family)
        out.append({
            "id": piece, "name": "Port " + str(port) + " availability", "ok": state == "ok",
            "detail": detail, "installable": False, "commands": commands,
        })
    return {"family": family, "label": label, "items": out}


def _dhd_install_argv(piece, family):
    if piece == "openssl":
        if family == "debian":
            return ["apt-get update", "apt-get install -y openssl"]
        if family == "fedora":
            return ["dnf install -y openssl"]
        if family == "arch":
            return ["pacman -S --needed --noconfirm openssl"]
    return []


def _dhd_run_install_command(command, sudo_password=""):
    if os.geteuid() == 0:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300, cwd=shell_cwd())
        return r.returncode, (r.stdout + r.stderr).strip()
    result = run_shell("sudo " + command, timeout=300, sudo=True, sudo_password=sudo_password)
    return int(result.get("exit_code", 1)), str(result.get("output", "")).strip()


def dhd_install_prereqs(pieces=None, sudo_password=""):
    check = dhd_prereq_check()
    by_id = {item["id"]: item for item in check["items"]}
    wanted = pieces or [item["id"] for item in check["items"] if not item["ok"] and item["installable"]]
    results = []
    for piece in wanted:
        item = by_id.get(piece)
        if item is None:
            continue
        if item["ok"]:
            results.append({"id": piece, "ok": True, "detail": item["name"] + " is already present.", "output": "", "commands": item["commands"]})
            continue
        if piece in DHD_SIM_INSTALL_FAIL:
            results.append({"id": piece, "ok": False, "detail": "The install step for " + item["name"] + " failed (diagnostics override). Nothing else was changed.", "output": "Apex forced this install to fail so the manual remedy can be verified.", "commands": item["commands"]})
            continue
        output = ""
        ok = False
        try:
            if piece == "proxy":
                ok = "DhdProxyHandler" in globals() and hasattr(ssl, "SSLContext")
                if ok:
                    DHD_SIM_MISSING.discard("proxy")
                output = "Proxy component self-test passed." if ok else "Proxy component self-test still fails."
            elif piece == "openssl":
                commands = _dhd_install_argv(piece, check["family"])
                if not commands:
                    output = "This distro family has no automatic package step in Apex."
                else:
                    codes = []
                    chunks = []
                    for command in commands:
                        code, text = _dhd_run_install_command(command, sudo_password)
                        codes.append(code)
                        if text:
                            chunks.append(text[-1200:])
                    output = "\n".join(chunks)
                    ok = all(code == 0 for code in codes) and bool(shutil.which("openssl"))
                    if ok:
                        DHD_SIM_MISSING.discard("openssl")
            elif piece == "certhome":
                try:
                    os.makedirs(DHD_DIR, exist_ok=True)
                    probe = os.path.join(DHD_DIR, ".apex-write-test-" + str(os.getpid()) + "-" + str(threading.get_ident()) + "-" + str(time.time_ns()))
                    with open(probe, "w") as f:
                        f.write("ok")
                    os.unlink(probe)
                    ok = True
                    output = "Certificate home created and verified writable."
                except Exception:
                    if os.geteuid() != 0 or sudo_password:
                        cmd = "install -d -o " + str(os.getuid()) + " -g " + str(os.getgid()) + ' "' + DHD_DIR + '"' 
                        code, text = _dhd_run_install_command(cmd, sudo_password)
                        output = text
                        if code == 0:
                            DHD_SIM_MISSING.discard("certhome")
                            DHD_SIM_MISSING.discard("cert-home")
                            return dhd_install_prereqs([piece], sudo_password)
                    else:
                        output = "The bridge could not create or write the certificate home."
                if ok:
                    DHD_SIM_MISSING.discard("certhome")
                    DHD_SIM_MISSING.discard("cert-home")
            else:
                output = "This prerequisite has no automatic install step."
        except Exception as e:
            output = str(e)
            ok = False
        results.append({
            "id": piece, "ok": bool(ok),
            "detail": (item["name"] + " installed and verified.") if ok else ("The install step for " + item["name"] + " failed. Nothing else was changed."),
            "output": output[-2400:], "commands": item["commands"],
        })
    return {"ok": all(r["ok"] for r in results) if results else True, "results": results, "prereqs": dhd_prereq_check()}


def _ops_load():
    global OPS_LOADED
    if OPS_LOADED:
        return
    OPS_LOADED = True
    try:
        with open(OPS_PATH) as f:
            data = json.load(f)
        rows = data.get("operations", []) if isinstance(data, dict) else []
        for op in rows:
            if isinstance(op, dict) and op.get("id"):
                OPS[op["id"]] = op
    except Exception:
        pass


def _ops_save():
    try:
        os.makedirs(os.path.dirname(OPS_PATH), exist_ok=True)
        rows = list(OPS.values())[-25:]
        tmp = OPS_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"operations": rows}, f)
        os.replace(tmp, OPS_PATH)
    except Exception:
        pass


def op_snapshot(op_id):
    _ops_load()
    with OPS_LOCK:
        op = OPS.get(op_id)
        return json.loads(json.dumps(op)) if op else None


def op_latest(kind=None):
    _ops_load()
    with OPS_LOCK:
        rows = list(OPS.values())
        if kind:
            rows = [op for op in rows if op.get("kind") == kind]
        return json.loads(json.dumps(rows[-1])) if rows else None


def op_new(kind, title, step_defs, source=""):
    _ops_load()
    op_id = "op-" + str(int(time.time() * 1000)) + "-" + secrets.token_hex(2)
    op = {
        "id": op_id, "kind": kind, "title": title, "source": source,
        "state": "running", "detail": "", "createdAt": int(time.time() * 1000),
        "updatedAt": int(time.time() * 1000),
        "steps": [{"id": sid, "name": name, "state": "pending", "detail": "", "commands": [], "output": ""} for sid, name in step_defs],
    }
    with OPS_LOCK:
        OPS[op_id] = op
        _ops_save()
    return op_id


def op_set(op_id, step_id, state, detail=None, commands=None, output=None, op_state=None):
    _ops_load()
    with OPS_LOCK:
        op = OPS.get(op_id)
        if not op:
            return
        for step in op.get("steps", []):
            if step.get("id") == step_id:
                step["state"] = state
                if detail is not None:
                    step["detail"] = detail
                if commands is not None:
                    step["commands"] = commands
                if output is not None:
                    step["output"] = output[-2400:]
                break
        if op_state:
            op["state"] = op_state
        op["updatedAt"] = int(time.time() * 1000)
        _ops_save()


def op_finish(op_id, state, detail):
    _ops_load()
    with OPS_LOCK:
        op = OPS.get(op_id)
        if not op:
            return
        op["state"] = state
        op["detail"] = detail
        op["updatedAt"] = int(time.time() * 1000)
        _ops_save()


def _dhd_op_fail(op_id, step_id, detail, commands=None):
    op_set(op_id, step_id, "failed", detail, commands=commands or [])
    op_finish(op_id, "failed", detail)


def _dhd_release_waiting_ops(ok, detail, commands=None):
    _ops_load()
    with OPS_LOCK:
        candidates = [op for op in OPS.values() if op.get("kind") == "dhd-enable" and op.get("state") == "waiting"]
    for op in candidates:
        OP_RESUME[op["id"]] = {"ok": bool(ok), "detail": detail, "commands": commands or []}
        event = OP_EVENTS.get(op["id"])
        if event:
            event.set()


def _run_dhd_enable_op(op_id, sudo_password=""):
    try:
        cfg = load_config()
        if dhd_settings(cfg)["enabled"] and DHD_STATE.get("running"):
            for step_id in ("prerequisites", "certificate", "proxy", "reachability"):
                op_set(op_id, step_id, "done", "Already live.")
            op_finish(op_id, "done", "DHD is already on.")
            return
        op_set(op_id, "prerequisites", "running", "Checking the proxy component, OpenSSL, certificate home, and ports 80/443.")
        check = dhd_prereq_check()
        missing = [item for item in check["items"] if not item["ok"]]
        installable = [item for item in missing if item["installable"]]
        blockers = [item for item in missing if not item["installable"]]
        if installable:
            names = ", ".join(item["name"] for item in installable)
            event = threading.Event()
            OP_EVENTS[op_id] = event
            op_set(op_id, "prerequisites", "waiting", "Missing: " + names + ". Use Install on this card or the DHD page; the enable continues automatically afterward.", op_state="waiting")
            event.wait()
            resume = OP_RESUME.pop(op_id, {"ok": False, "detail": "The install step did not report a result.", "commands": []})
            OP_EVENTS.pop(op_id, None)
            if not resume.get("ok"):
                _dhd_op_fail(op_id, "prerequisites", resume.get("detail") or "A prerequisite install failed.", resume.get("commands") or [])
                return
            check = dhd_prereq_check()
            missing = [item for item in check["items"] if not item["ok"]]
            blockers = [item for item in missing if not item["installable"]]
            installable = [item for item in missing if item["installable"]]
            if installable:
                commands = []
                for item in installable:
                    commands.extend(item["commands"])
                _dhd_op_fail(op_id, "prerequisites", "A prerequisite is still missing after the install step: " + ", ".join(item["name"] for item in installable), commands)
                return
        if blockers:
            commands = []
            detail_bits = []
            for item in blockers:
                commands.extend(item["commands"])
                detail_bits.append(item["name"] + ": " + item["detail"])
            _dhd_op_fail(op_id, "prerequisites", " ".join(detail_bits), commands)
            return
        op_set(op_id, "prerequisites", "done", "Every prerequisite is present.")
        cfg = load_config()
        dhd_save(cfg, {"enabled": True})
        ensure_access_code(cfg)
        cfg = load_config()
        if ACTIVE_BIND_HOST == "0.0.0.0":
            op_set(op_id, "certificate", "waiting", "The bridge is restarting onto loopback-only before the public proxy opens.", op_state="waiting")
            op_finish(op_id, "waiting", "Bridge restart requested; this operation resumes when the new bridge answers.")
            schedule_bridge_restart()
            return

        def progress(step_id, state, detail, commands=None):
            op_set(op_id, step_id, state, detail, commands=commands or [])

        ok = dhd_bring_up(cfg, progress=progress)
        cfg = load_config()
        payload = dhd_state_payload(cfg, True)
        if ok:
            op_set(op_id, "reachability", "done", "Local check passed: the proxy answered on 443 on this machine (answered on this machine). Outside reach is reported separately on the DHD page." + (" The domain certificate is still pending; the door is answering on the self-signed certificate meanwhile." if payload.get("certPending") else ""))
            summary = _dhd_on_summary(payload)
            op_finish(op_id, "done", summary)
        else:
            detail = DHD_STATE.get("last_error") or "DHD did not come up."
            op_finish(op_id, "failed", detail)
    except Exception as e:
        op_finish(op_id, "failed", "DHD enable failed: " + str(e))


def dhd_start_enable_operation(source, sudo_password=""):
    existing = op_latest("dhd-enable")
    if existing and existing.get("state") in ("running", "waiting"):
        return existing["id"]
    op_id = op_new("dhd-enable", "Turn on DHD", [
        ("prerequisites", "Prerequisites"), ("certificate", "Certificate"),
        ("proxy", "Reverse proxy"), ("reachability", "Reachability check"),
    ], source=source)
    threading.Thread(target=_run_dhd_enable_op, args=(op_id, sudo_password), daemon=True).start()
    return op_id


def dhd_resume_enable_operation():
    op = op_latest("dhd-enable")
    if not op or op.get("state") not in ("waiting", "running"):
        return
    cfg = load_config()
    if not dhd_settings(cfg)["enabled"]:
        return
    if DHD_STATE.get("running"):
        payload = dhd_state_payload(cfg, True)
        op_set(op["id"], "prerequisites", "done", "Every prerequisite is present.")
        op_set(op["id"], "certificate", "done", "Certificate ready (" + payload.get("mode", "self-signed") + ").")
        op_set(op["id"], "proxy", "done", "The proxy is listening on 80/443.")
        op_set(op["id"], "reachability", "done", "Local check passed: the proxy answered on 443 on this machine (answered on this machine).")
        op_finish(op["id"], "done", _dhd_on_summary(payload))
    elif DHD_STATE.get("last_error"):
        detail = DHD_STATE["last_error"]
        stage = "proxy" if "proxy step" in detail else "reachability" if "self-check" in detail else "certificate"
        op_set(op["id"], stage, "failed", detail, commands=dhd_failure_commands(stage, detail, dhd_settings(cfg)["domain"]))
        op_finish(op["id"], "failed", detail)


def dhd_chat_intent(text):
    raw = str(text or "").strip()
    low = " " + re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip() + " "
    if " dhd " not in low:
        return None
    if re.match(r"\s*(how|what|why|explain)\b", raw, re.I):
        return None
    if re.search(r"\b(turn off|switch off|disable|stop|shut off)\b", low):
        return "disable"
    if re.search(r"\b(turn on|switch on|enable|start|open|activate|set up|setup)\b", low):
        return "enable"
    return None


# --- Navi Mesh — Ring 1 (build .85, issue #78) -------------------
# Navi Mesh is pooled inference across the operator's own machines:
# a stronger machine answers for a weaker one. Routing is whole-
# request: the borrower assembles the prompt exactly as it would
# for its own model (persona, Vault, RAG, history) and a paired
# lender's model writes the whole reply. Alex's rulings from the
# design call govern the defaults: borrowing is AUTOMATIC for
# paired peers once Mesh is on, with an off switch (R1); nothing
# anywhere is tied to a specific operator, machine, or domain —
# every name and address comes from config and peer cards (R2);
# a lender that drops mid-answer raises a notice AND the request
# falls back to a fresh local reply, never spliced prose (R3);
# lending is automatic when idle with an off switch that aborts
# an in-flight borrowed generation immediately (R4); a busy
# refusal gets a short configurable grace before local fallback,
# and the lender is only ever claimed on the NEXT request (R5).
#
# Hard rules (spec sections 4.3 and 7): /mesh/* is never part of
# the passcode-cookie dashboard surface — the DHD proxy hands it
# to this section directly, before its cookie gate; node keys and
# dashboard codes share no credentials in either direction; and
# the lender persists NOTHING but ledger metadata — no prompt or
# reply text is ever written to disk on the lending side.

MESH_DIR = os.path.join(ROOT, "config", "mesh")
MESH_KEY_PATH = os.path.join(MESH_DIR, "node_key.pem")
MESH_PUB_PATH = os.path.join(MESH_DIR, "node_pub.pem")
MESH_CERT_PATH = os.path.join(MESH_DIR, "cert.pem")
MESH_CERT_KEY_PATH = os.path.join(MESH_DIR, "cert_key.pem")
MESH_LEDGER_PATH = os.path.join(MESH_DIR, "ledger.jsonl")
# Where restored pairing-card pictures land (Build 9, #89): the
# GitHub backup's Mesh pairing cards restore into this folder —
# the pictures stay importable files, and the peer pictures are
# also re-paired through the normal card check on import.
MESH_CARDS_DIR = os.path.join(MESH_DIR, "cards")

MESH_LOCK = threading.Lock()
MESH_STATE = {
    # Lender side: the in-flight borrowed generation, if any. The
    # connection object is kept so instant-off can abort it by
    # closing the socket (R4: OFF means OFF mid-generation too).
    "borrowed_conn": None,
    "borrowed_resp": None,
    "borrowed_peer": "",
    "borrowed_started": 0.0,
    "lend_stop_stamp": 0.0,
    # Local generations in flight on this machine (either role) —
    # the busy/idle signals admission and status read.
    "local_gen": 0,
    "last_local_done": 0.0,
    "last_borrowed_done": 0.0,
    # Borrower side: an outbound borrowed generation in flight.
    "borrow_out": False,
    "borrow_peer": "",
    # Reachability probe cache: nodeId -> (stamp, status-or-None,
    # error-kind). Status probes are short and chat is latency-
    # sensitive, so a probe is reused for a few seconds.
    "probe_cache": {},
    # Borrower side (build .87): nodeId -> stamp of the last
    # in-flight DROP this machine suffered from that peer — the
    # status payload's "dropped" peer state and the Servers row's
    # warning read it. A later successful probe supersedes it,
    # and a borrow the peer actually serves clears it outright.
    "peer_dropped": {},
    # Background peer health (Build 7, #87): whether the health
    # thread has been started, and nodeId -> the last health
    # state word the bridge LOGGED for that peer ("reachable" or
    # "unreachable:<kind>"). Only transitions are logged, so the
    # word lives here to compare against — the probe cache above
    # stays the status payload's source of truth.
    "health_started": False,
    "peer_health": {},
}
MESH_SERVERS = []


def _mesh_int(value, fallback):
    try:
        return int(value)
    except Exception:
        return fallback


def _mesh_peer(p):
    # One peer record, normalized. Addresses keep the operator's
    # order — LAN first as listed on the card (spec section 3.1).
    if not isinstance(p, dict):
        return None
    addrs = p.get("addresses")
    if not isinstance(addrs, list):
        addrs = []
    addrs = [str(a).strip() for a in addrs if str(a).strip()]
    return {
        "name": str(p.get("name") or "Unnamed peer"),
        "addresses": addrs,
        "port": _mesh_int(p.get("port"), 8765),
        "nodeId": str(p.get("nodeId") or ""),
        "publicKeyPem": str(p.get("publicKeyPem") or ""),
        "certFingerprint": str(p.get("certFingerprint") or "").strip().lower(),
        "canBorrow": p.get("canBorrow") is not False,
        "capabilities": _mesh_caps_sanitize(p.get("capabilities")),
    }


def _mesh_caps_sanitize(raw):
    # A peer's capability self-report, cut down to short strings
    # and numbers only (build .86): a card is operator-carried
    # data, so nothing long, nested, or structural survives into
    # the stored record or the roster. None when absent.
    if not isinstance(raw, dict):
        return None
    def s(v, n=80):
        t = str(v or "").strip()
        if len(t) <= n:
            return t
        # Cut at a word boundary: a capability line must never
        # slice a word in half on the roster.
        cut = t[:n].rsplit(" ", 1)[0]
        return (cut or t[:n]) + "…"
    def num(v):
        try:
            return float(v)
        except Exception:
            return 0
    def i(v):
        try:
            return int(v)
        except Exception:
            return 0
    caps = raw.get("caps") if isinstance(raw.get("caps"), dict) else {}
    def cap_i(v, fallback):
        # Build 7 (Fix F): the caps on a card are the peer's
        # CONFIGURED values. A card that does not state them (one
        # written before caps rode along, or a hand-trimmed one)
        # falls back to the shipped defaults — a stated value
        # under 1 is not a real configuration (the settings save
        # validates 1..100 / 1..10000), so it reads as unstated
        # rather than as "lends at most 0%".
        n = i(v)
        return n if n >= 1 else fallback
    return {
        "hardwareClass": s(raw.get("hardwareClass"), 60),
        "gpu": s(raw.get("gpu")),
        "cpu": s(raw.get("cpu")),
        "ramGB": num(raw.get("ramGB")),
        "model": s(raw.get("model"), 24) or "navi",
        "speedClass": s(raw.get("speedClass"), 40),
        # A card written before the posture rode along (Build 6
        # and earlier) was an idle-only lender by construction —
        # absent reads as True, the posture those builds kept.
        "idleOnly": raw.get("idleOnly") is not False,
        "caps": {
            "maxSharePercent": cap_i(caps.get("maxSharePercent"), 25),
            "maxGenerationsPerHour": cap_i(caps.get("maxGenerationsPerHour"), 20),
        },
    }


def mesh_capabilities(cfg):
    # This node's capability self-report (build .86): an honest
    # summary of THIS machine from its own data — the stored
    # hardware profile (detected GPU kind/name, CPU model, total
    # RAM, tier) and the lend settings as caps. The model is
    # "navi"; the speed class derives from the GPU situation:
    # discrete GPU -> "GPU-accelerated", integrated ->
    # "Integrated graphics", none -> "CPU".
    ms = mesh_settings(cfg)
    hp = cfg.get("hardware_profile") if isinstance(cfg, dict) else None
    det = hp.get("detected") if isinstance(hp, dict) else {}
    if not isinstance(det, dict):
        det = {}
    gpu_kind = str(det.get("gpuKind") or "none").strip().lower()
    gpu_name = str(det.get("gpuName") or "").strip()[:80]
    cpu = str(det.get("cpuModel") or "").strip()[:80]
    try:
        ram = float(det.get("totalRamGB") or 0)
    except Exception:
        ram = 0
    tier = ""
    if isinstance(hp, dict):
        tier = str(hp.get("tierLabel") or hp.get("tier") or "").strip()[:60]
    if gpu_kind == "discrete":
        speed = "GPU-accelerated"
        gpu = gpu_name or "Discrete GPU"
    elif gpu_kind == "integrated":
        speed = "Integrated graphics"
        gpu = gpu_name or "Integrated graphics"
    else:
        speed = "CPU"
        gpu = ""
    return {
        "hardwareClass": tier,
        "gpu": gpu,
        "cpu": cpu,
        "ramGB": ram,
        "model": "navi",
        "speedClass": speed,
        # Build 7 (Fix F2): the idle posture rides the same
        # self-report as the caps, so a peer's card and roster
        # line state it truthfully — "lends when idle" vs "lends
        # even while busy" — from this machine's own setting.
        "idleOnly": ms["lend"]["idleOnly"],
        "caps": {
            "maxSharePercent": ms["lend"]["maxSharePercent"],
            "maxGenerationsPerHour": ms["lend"]["maxGenerationsPerHour"],
        },
    }


def mesh_settings(cfg):
    # Absent-block-safe, like dhd_settings: an install whose config
    # predates the mesh block (or a field of it) reads as the
    # shipped defaults — absent = off.
    m = cfg.get("mesh") if isinstance(cfg, dict) else None
    if not isinstance(m, dict):
        m = {}
    borrow = m.get("borrow") if isinstance(m.get("borrow"), dict) else {}
    lend = m.get("lend") if isinstance(m.get("lend"), dict) else {}
    role = str(m.get("role") or "both").strip().lower()
    if role not in ("borrow", "lend", "both"):
        role = "both"
    peers = []
    raw_peers = borrow.get("peers")
    if isinstance(raw_peers, list):
        for p in raw_peers:
            peer = _mesh_peer(p)
            if peer is not None:
                peers.append(peer)
    return {
        "enabled": m.get("enabled") is True,
        "role": role,
        "nodeName": str(m.get("nodeName") or ""),
        "borrow": {
            # R1: borrowing defaults ON under the master switch.
            "enabled": borrow.get("enabled") is not False,
            "graceMs": _mesh_int(borrow.get("graceMs"), 2000),
            "peers": peers,
        },
        "lend": {
            "enabled": lend.get("enabled") is True,
            "maxSharePercent": _mesh_int(lend.get("maxSharePercent"), 25),
            "maxGenerationsPerHour": _mesh_int(lend.get("maxGenerationsPerHour"), 20),
            "perPeerPerHour": _mesh_int(lend.get("perPeerPerHour"), 10),
            "idleOnly": lend.get("idleOnly") is not False,
            "idleAfterSeconds": _mesh_int(lend.get("idleAfterSeconds"), 60),
        },
        "port": _mesh_int(m.get("port"), 8765),
        "nodeId": str(m.get("nodeId") or ""),
        "ledger": m.get("ledger") is not False,
        "ledgerInBackup": m.get("ledgerInBackup") is True,
    }


# -- Node identity (spec section 4.2) -------------------------------
# An Ed25519 keypair under config/mesh/, made with the openssl
# binary — stdlib Python has no Ed25519, and openssl is already a
# DHD prerequisite. The private key never leaves this machine: it
# appears in no payload, no card, and no backup item.

def mesh_openssl_missing_error():
    return (
        "Apex Mesh needs the openssl program to create this machine's node key, "
        "and openssl was not found on this machine. Install openssl (the same "
        "prerequisite DHD uses) and try again."
    )


def _mesh_pub_der(pub_pem):
    # The DER bytes of a PEM public key, via openssl — the nodeId
    # is the SHA-256 of exactly these bytes.
    fd, path = tempfile.mkstemp(suffix=".pem")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(pub_pem)
        r = subprocess.run(
            ["openssl", "pkey", "-pubin", "-in", path, "-outform", "DER"],
            capture_output=True, timeout=30,
        )
        if r.returncode != 0:
            return b""
        return r.stdout
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def mesh_node_id():
    if os.path.exists(MESH_PUB_PATH):
        der = _mesh_pub_der(read_file(MESH_PUB_PATH))
        if der:
            return hashlib.sha256(der).hexdigest()
    return ""


def mesh_ensure_identity(cfg):
    # Generates the keypair on first Mesh enable and records the
    # nodeId in the config. Returns (ok, error-in-plain-words).
    if shutil.which("openssl") is None:
        return False, mesh_openssl_missing_error()
    try:
        os.makedirs(MESH_DIR, exist_ok=True)
        if not (os.path.exists(MESH_KEY_PATH) and os.path.exists(MESH_PUB_PATH)):
            r = subprocess.run(
                ["openssl", "genpkey", "-algorithm", "ED25519", "-out", MESH_KEY_PATH],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                return False, "openssl could not create the Mesh node key: " + (r.stderr or "").strip()[:200]
            r = subprocess.run(
                ["openssl", "pkey", "-in", MESH_KEY_PATH, "-pubout", "-out", MESH_PUB_PATH],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                return False, "openssl could not write the Mesh node public key: " + (r.stderr or "").strip()[:200]
            try:
                os.chmod(MESH_KEY_PATH, 0o600)
            except Exception:
                pass
        node_id = mesh_node_id()
        if not node_id:
            return False, "The Mesh node key exists but could not be read back — check config/mesh/ on this machine."
        block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
        block = dict(block)
        if block.get("nodeId") != node_id:
            block["nodeId"] = node_id
            cfg["mesh"] = block
            save_config(cfg)
        return True, ""
    except Exception as e:
        return False, "Mesh identity could not be set up: " + str(e)


def mesh_sign(data):
    # Ed25519 signature (base64) over data, with this node's key.
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        r = subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-inkey", MESH_KEY_PATH, "-rawin", "-in", path],
            capture_output=True, timeout=30,
        )
        if r.returncode != 0:
            raise RuntimeError("openssl could not sign the Mesh request")
        return base64.b64encode(r.stdout).decode()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def mesh_verify(pub_pem, data, sig_b64):
    # Verify an Ed25519 signature against a peer's pinned public
    # key. Any doubt at all reads as failure.
    try:
        sig = base64.b64decode(sig_b64 or "")
    except Exception:
        return False
    paths = []
    try:
        for blob, suffix in ((pub_pem.encode(), ".pem"), (data, ".bin"), (sig, ".sig")):
            fd, path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                f.write(blob)
            paths.append(path)
        r = subprocess.run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", paths[0],
             "-rawin", "-in", paths[1], "-sigfile", paths[2]],
            capture_output=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False
    finally:
        for path in paths:
            try:
                os.unlink(path)
            except Exception:
                pass


def mesh_sig_payload(request_id, ts, body):
    # The signed string (spec section 4.3): requestId, timestamp,
    # and the body's SHA-256, one per line.
    return (
        str(request_id) + "\n" + str(ts) + "\n"
        + hashlib.sha256(body or b"").hexdigest()
    ).encode()


def mesh_signed_headers(request_id, body):
    ts = str(int(time.time()))
    return {
        "X-Mesh-Node": mesh_node_id(),
        "X-Mesh-Ts": ts,
        "X-Mesh-Sig": mesh_sign(mesh_sig_payload(request_id, ts, body)),
        "Content-Type": "application/json",
    }


def mesh_authenticate(handler, body, request_id):
    # Verifies a signed Mesh request against the paired-peer list.
    # Returns the peer record, or None — the caller answers a bare
    # "unauthorized" either way; WHY it failed never leaves here
    # (spec section 4.3: no detail leakage).
    # Build 7 (#87): pairing is the whole consent on this side —
    # any peer on the paired list with a valid key and signature
    # is authorized. The peer record's canBorrow flag used to be
    # required here too, which made one flag do two opposite jobs:
    # a lender whose stored flag for the requester was off refused
    # even a health probe as "unauthorized", invisibly. canBorrow
    # now means one thing only, enforced on the BORROWING side in
    # mesh_try_borrow: this machine will not borrow from a peer
    # whose flag is off.
    node = handler.headers.get("X-Mesh-Node") or ""
    ts = handler.headers.get("X-Mesh-Ts") or ""
    sig = handler.headers.get("X-Mesh-Sig") or ""
    if not node or not ts or not sig:
        return None
    try:
        ts_i = int(ts)
    except Exception:
        return None
    if abs(time.time() - ts_i) > 120:
        return None
    ms = mesh_settings(load_config())
    peer = None
    for p in ms["borrow"]["peers"]:
        if p["nodeId"] == node:
            peer = p
    if peer is None or not peer["publicKeyPem"]:
        return None
    if not mesh_verify(peer["publicKeyPem"], mesh_sig_payload(request_id, ts, body), sig):
        return None
    return peer


# -- Mesh certificate (spec section 4.1) ----------------------------
# Mesh carries its OWN self-signed certificate under config/mesh/,
# made the same way DHD makes its — always (build .86): the
# dedicated Mesh door has its own identity in every configuration,
# so the fingerprint a peer pins from the card is the Mesh cert's
# whether or not DHD is on. The borrower PINS the certificate's
# SHA-256 fingerprint from the peer card — that pin, not a CA, is
# what authenticates the door.

def mesh_active_cert():
    # (cert_path, key_path) this node serves Mesh on: the Mesh
    # self-signed pair under config/mesh/, in all cases.
    return MESH_CERT_PATH, MESH_CERT_KEY_PATH


def mesh_ensure_cert():
    cert_path, _key_path = mesh_active_cert()
    if cert_path == MESH_CERT_PATH and not os.path.exists(MESH_CERT_PATH):
        if shutil.which("openssl") is None:
            return False, mesh_openssl_missing_error()
        os.makedirs(MESH_DIR, exist_ok=True)
        sans = ["DNS:localhost", "IP:127.0.0.1"]
        try:
            ip = lan_ipv4()
            if ip and ip != "127.0.0.1":
                sans.append("IP:" + ip)
        except Exception:
            pass
        r = subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048",
             "-keyout", MESH_CERT_KEY_PATH, "-out", MESH_CERT_PATH,
             "-days", "365", "-nodes", "-subj", "/CN=Apex Mesh",
             "-addext", "subjectAltName=" + ",".join(sans)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return False, "openssl could not generate the Mesh certificate: " + (r.stderr or "").strip()[:200]
    return True, ""


def mesh_cert_fingerprint():
    cert_path, _key_path = mesh_active_cert()
    if not os.path.exists(cert_path):
        ok, _err = mesh_ensure_cert()
        if not ok:
            return ""
    try:
        r = subprocess.run(
            ["openssl", "x509", "-in", cert_path, "-outform", "DER"],
            capture_output=True, timeout=30,
        )
        if r.returncode != 0 or not r.stdout:
            return ""
        return hashlib.sha256(r.stdout).hexdigest()
    except Exception:
        return ""


# -- Peer card (spec section 3.1) -----------------------------------

def _interface_ipv4s():
    # Every non-loopback IPv4 address on this machine's network
    # interfaces, via the SIOCGIFADDR ioctl (stdlib only; Linux is
    # the bridge's platform). Best-effort by construction: any
    # failure — no fcntl, an interface that will not answer —
    # simply contributes nothing, and the caller keeps the
    # default-route address it already has. Card plumbing only:
    # these addresses are never rendered or logged anywhere.
    out = []
    try:
        import fcntl
        import struct
        for _idx, name in socket.if_nameindex():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    packed = fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", name.encode()[:15]))
                finally:
                    s.close()
                ip = socket.inet_ntoa(packed[20:24])
            except Exception:
                continue
            if ip and not ip.startswith("127.") and ip not in out:
                out.append(ip)
    except Exception:
        pass
    return out


def mesh_card(cfg):
    # This node's card data — the payload the PNG pairing picture
    # is minted from (build_mesh_card_png). The operator carries
    # the PICTURE to their other machine by hand; since Build 9
    # (#90) the card never leaves as copyable text. Names and
    # addresses come from config and this machine only (R2 —
    # nothing baked in).
    ms = mesh_settings(cfg)
    addresses = []
    try:
        ip = lan_ipv4()
        if ip and ip != "127.0.0.1":
            addresses.append(ip)
    except Exception:
        pass
    # Build 7 (#87): the card used to freeze the ONE address the
    # default route picked at render time — the field card that
    # carried a hotspot-range address beside a dead pairing. When
    # the machine has more than one non-loopback address, the
    # card now carries them all, the default-route (LAN) address
    # first and the rest after; the borrower tries them in order,
    # so one stale address can no longer strand the pair.
    for ip in _interface_ipv4s():
        if ip not in addresses:
            addresses.append(ip)
    d = cfg.get("dhd") if isinstance(cfg.get("dhd"), dict) else {}
    domain = str(d.get("domain") or "").strip()
    if domain and d.get("enabled") is True:
        addresses.append(domain)
    addresses.append("127.0.0.1")
    name = ms["nodeName"] or socket.gethostname()
    return {
        "meshCard": 1,
        "name": name,
        "nodeId": mesh_node_id(),
        "publicKeyPem": read_file(MESH_PUB_PATH).strip(),
        "certFingerprint": mesh_cert_fingerprint(),
        "addresses": addresses,
        "port": ms["port"],
        "capabilities": mesh_capabilities(cfg),
    }


def mesh_parse_card(text):
    # Validates card data. Since Build 9 (#90) the only caller
    # is the PNG picture path (parse_mesh_card_png), which reads
    # the card out of the picture and passes it here — one
    # validator for every pairing. Returns (peer, error) —
    # errors in plain words, because a bare "invalid" helps
    # nobody.
    try:
        card = json.loads(text or "")
    except Exception:
        return None, "That does not look like a Mesh card — the card data is not in the shape a pairing card carries. Download a fresh PNG card from the other machine's Mesh page and try that picture."
    if not isinstance(card, dict) or card.get("meshCard") != 1:
        return None, "That does not look like a Mesh card — the card data is not in the shape a pairing card carries. Download a fresh PNG card from the other machine's Mesh page and try that picture."
    fp = str(card.get("certFingerprint") or "").strip().lower()
    if len(fp) != 64 or any(c not in "0123456789abcdef" for c in fp):
        return None, "The card's certificate fingerprint is not in the right shape — the picture's card data is damaged. Download a fresh PNG card from the other machine and try again."
    node_id = str(card.get("nodeId") or "").strip()
    if len(node_id) != 64:
        return None, "The card's node id is not in the right shape — the picture's card data is damaged. Download a fresh PNG card from the other machine and try again."
    if not str(card.get("publicKeyPem") or "").strip():
        return None, "The card is missing its public key — the picture's card data is damaged. Download a fresh PNG card from the other machine and try again."
    peer = _mesh_peer({
        "name": card.get("name"),
        "addresses": card.get("addresses"),
        "port": card.get("port"),
        "nodeId": node_id,
        "publicKeyPem": card.get("publicKeyPem"),
        "certFingerprint": fp,
        "canBorrow": True,
        "capabilities": card.get("capabilities"),
    })
    if peer is None or not peer["addresses"]:
        return None, "The card carries no address to reach the other machine at — download a fresh PNG card from the other machine and try again."
    return peer, ""


def mesh_add_peer(cfg, peer):
    # Adds a validated peer record to this machine's pairings —
    # the shared tail of the pairing path (the PNG picture card,
    # the only path since Build 9): pairing is the consent act,
    # a record
    # with the same nodeId is replaced rather than duplicated,
    # and the config is saved before the caller answers. Returns
    # an error string, or "" when the peer is in. The caller
    # probes at once (mesh_probe_peers_soon) after a success.
    if peer["nodeId"] and peer["nodeId"] == mesh_node_id():
        return "That is this machine's own card — a machine does not pair with itself."
    block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
    block = dict(block)
    borrow = block.get("borrow") if isinstance(block.get("borrow"), dict) else {}
    borrow = dict(borrow)
    peers = borrow.get("peers") if isinstance(borrow.get("peers"), list) else []
    peers = [p for p in peers if not (isinstance(p, dict) and str(p.get("nodeId") or "") == peer["nodeId"])]
    peers.append(peer)
    borrow["peers"] = peers
    block["borrow"] = borrow
    cfg["mesh"] = block
    save_config(cfg)
    return ""


# -- The pairing card as a picture (Build 7, spec section 13) ----
# The card's second body: a real .png whose face a person can
# read — the machine's name, its node identity, and the offer in
# words (capabilities, the lending limits it is CONFIGURED with,
# its idle posture) — while the whole card rides inside the
# picture as a tEXt payload, the same data-in-picture convention
# the chip cartridges use (keyword, NUL, JSON), so Apex keeps ONE
# picture format. The face is drawn from the very dict that
# becomes the payload, so the picture can never advertise an
# offer the payload does not make; and the payload is the card
# itself, so a PNG pairing lands the peer record whole.

_MESH_CARD_FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "•": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    "[": ("..###", "..#..", "..#..", "..#..", "..#..", "..#..", "..###"),
    "]": ("###..", "..#..", "..#..", "..#..", "..#..", "..#..", "###.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#....", ".####", "....."),
}


def _mesh_face_clean(text):
    # Words for the card face: uppercase, in the characters the
    # face font carries; anything else becomes a space, and the
    # typographic dashes and dots fold to the drawn ones.
    out = []
    for ch in str(text or "").upper():
        if ch in ("·", "∙"):
            out.append("•")
        elif ch in ("—", "–"):
            out.append("-")
        elif ch in _MESH_CARD_FONT:
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


def _mesh_face_wrap(text, max_chars):
    lines = []
    cur = ""
    for word in str(text or "").split(" "):
        if not word:
            continue
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = cur + " " + word if cur else word
    if cur:
        lines.append(cur)
    return lines


def _mesh_face_text_w(text, scale):
    return len(text) * 6 * scale


def _mesh_face_draw(img, W, H, x, y, text, scale, rgb):
    cx = x
    for ch in text:
        glyph = _MESH_CARD_FONT.get(ch) or _MESH_CARD_FONT["?"]
        for gy in range(7):
            row = glyph[gy] if gy < len(glyph) else ""
            for gx in range(5):
                if gx < len(row) and row[gx] == "#":
                    for sy in range(scale):
                        for sx in range(scale):
                            xx = cx + gx * scale + sx
                            yy = y + gy * scale + sy
                            if 0 <= xx < W and 0 <= yy < H:
                                o = (yy * W + xx) * 3
                                img[o] = rgb[0]
                                img[o + 1] = rgb[1]
                                img[o + 2] = rgb[2]
        cx += 6 * scale


def build_mesh_card_png(cfg):
    # This node's pairing card as a picture. Face and payload
    # both come from mesh_card(cfg) — one source, so what the
    # picture says is what the picture carries.
    return _mesh_card_png_render(mesh_card(cfg))


def build_mesh_peer_card_png(peer):
    # A paired peer's card as a picture, re-drawn from the stored
    # peer record (Build 9, #89). The record holds everything the
    # card carried — mesh_parse_card built it from the card — so
    # the re-drawn picture's payload is the same card, and it
    # imports to the identical record on any machine. This is
    # what the GitHub backup carries for peers: peers paired by a
    # pasted text card never had a picture to retain, so the
    # stored card is the one honest source for every peer alike.
    card = {
        "meshCard": 1,
        "name": peer.get("name"),
        "nodeId": peer.get("nodeId"),
        "publicKeyPem": peer.get("publicKeyPem"),
        "certFingerprint": peer.get("certFingerprint"),
        "addresses": peer.get("addresses"),
        "port": peer.get("port"),
        "capabilities": peer.get("capabilities"),
    }
    return _mesh_card_png_render(card)


def _mesh_card_png_render(card):
    # Draws one pairing-card picture from a card dict: the face a
    # person reads above, the whole card as the tEXt payload.
    caps = card.get("capabilities") if isinstance(card.get("capabilities"), dict) else {}
    cap_caps = caps.get("caps") if isinstance(caps.get("caps"), dict) else {}
    W, H = 720, 452
    BG = (10, 14, 18)
    RIM = (34, 48, 61)
    ACCENT = (34, 211, 238)
    INK = (230, 241, 245)
    DIM = (159, 179, 200)
    img = bytearray(bytes(BG) * (W * H))
    def px(x, y, rgb):
        if 0 <= x < W and 0 <= y < H:
            o = (y * W + x) * 3
            img[o] = rgb[0]
            img[o + 1] = rgb[1]
            img[o + 2] = rgb[2]
    for i in range(3):
        for x in range(W):
            px(x, i, RIM)
            px(x, H - 1 - i, RIM)
        for y in range(H):
            px(i, y, RIM)
            px(W - 1 - i, y, RIM)
    MX = 36
    y = 30
    _mesh_face_draw(img, W, H, MX, y, "NAVI MESH", 3, ACCENT)
    right = "PAIRING CARD"
    _mesh_face_draw(img, W, H, W - MX - _mesh_face_text_w(right, 3), y, right, 3, DIM)
    y += 21 + 22
    name = _mesh_face_clean(card.get("name") or "This machine") or "THIS MACHINE"
    scale = 5
    while scale > 2 and _mesh_face_text_w(name, scale) > W - 2 * MX:
        scale -= 1
    if _mesh_face_text_w(name, scale) > W - 2 * MX:
        name = name[: max(0, (W - 2 * MX) // (6 * scale) - 3)] + "..."
    _mesh_face_draw(img, W, H, MX, y, name, scale, INK)
    y += 7 * scale + 14
    _mesh_face_draw(img, W, H, MX, y, "NODE " + str(card.get("nodeId") or "")[:12], 2, DIM)
    y += 14 + 16
    for x in range(MX, W - MX):
        px(x, y, ACCENT)
        px(x, y + 1, ACCENT)
    y += 18
    _mesh_face_draw(img, W, H, MX, y, "THE OFFER", 2, ACCENT)
    y += 14 + 10
    bits = []
    if caps.get("hardwareClass"):
        bits.append(str(caps["hardwareClass"]))
    if caps.get("gpu"):
        bits.append(str(caps["gpu"]))
    elif caps.get("cpu"):
        bits.append(str(caps["cpu"]))
    if caps.get("ramGB"):
        try:
            ram = float(caps["ramGB"])
            bits.append((str(int(ram)) if ram == int(ram) else str(ram)) + " GiB RAM")
        except Exception:
            pass
    bits.append("model " + str(caps.get("model") or "navi"))
    if caps.get("speedClass"):
        bits.append(str(caps["speedClass"]))
    offer_lines = _mesh_face_wrap(_mesh_face_clean(" · ".join(bits)), 54)
    try:
        share = int(cap_caps.get("maxSharePercent") or 25)
    except Exception:
        share = 25
    try:
        gens = int(cap_caps.get("maxGenerationsPerHour") or 20)
    except Exception:
        gens = 20
    offer_lines.append("LENDS AT MOST " + str(share) + "% OF EACH HOUR")
    offer_lines.append(str(gens) + " GENERATIONS AN HOUR")
    offer_lines.append("LENDS WHEN IDLE" if caps.get("idleOnly") is not False else "LENDS EVEN WHILE BUSY")
    for line in offer_lines:
        _mesh_face_draw(img, W, H, MX, y, line, 2, INK)
        y += 14 + 6
    foot = _mesh_face_wrap(
        "THE PAIRING DATA RIDES INSIDE THIS PICTURE. SEND THE FILE ITSELF - "
        "INSIDE A .ZIP FOR CHAT APPS, WHICH RECOMPRESS PICTURES AND STRIP THE DATA OUT.",
        54,
    )
    fy = H - 26 - len(foot) * 20
    for line in foot:
        _mesh_face_draw(img, W, H, MX, fy, line, 2, DIM)
        fy += 14 + 6
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += img[yy * W * 3:(yy + 1) * W * 3]
    text = b"navi-mesh-card\x00" + json.dumps(card).encode()
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", text)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _png_chunk(b"IEND", b"")
    )


# The PNG import's refusals, in the operator's own words — each
# names what is wrong and what to do about it, because a picture
# that pairs nothing must never fail silently (Build 7, spec
# section 13, Alex's wording rule).
MESH_CARD_PNG_NOT_PNG = "That file is not a PNG image — a Mesh card travels as a .png picture. Export it again from the other machine's Mesh page (Download PNG card) and send the file itself."
MESH_CARD_PNG_NO_PAYLOAD = "This image has no readable Mesh card data — it may have been recompressed by a chat app, which strips the data out of the picture while leaving the picture itself looking fine. Send the original file inside a .zip instead."
MESH_CARD_PNG_DAMAGED = "This picture started life as a Mesh card, but the card data inside it is damaged — it no longer reads whole, so nothing was paired. Ask the other machine to export a fresh PNG card, and send the original file inside a .zip so nothing re-encodes it on the way."
MESH_CARD_PNG_IS_CHIP = "That picture is a Navi chip cartridge, not a Mesh pairing card — chips and cards are different pictures. Pairing cards come from the other machine's Mesh page: Download PNG card."
MESH_CARD_PNG_NEWER = "This picture's Mesh card was made by a newer Apex than this one — update this machine, then import the card again."


def parse_mesh_card_png(data):
    # Reads a pairing card back out of a PNG picture. Returns
    # (peer, error): on success the peer record mesh_parse_card
    # builds from the embedded block — the identical record the
    # text-card path builds, because the embedded payload goes
    # through that same validation; on failure one of the
    # specific refusals above. A tampered or truncated payload
    # fails loudly here: bad chunk CRC, broken JSON, or a card
    # that no longer validates is damage, never a quiet no.
    if not isinstance(data, (bytes, bytearray)) or len(data) < 8 or bytes(data[:8]) != b"\x89PNG\r\n\x1a\n":
        return None, MESH_CARD_PNG_NOT_PNG
    data = bytes(data)
    pos = 8
    payload = None
    saw_chip = False
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            return None, MESH_CARD_PNG_DAMAGED
        chunk_data = data[pos + 8:pos + 8 + length]
        if kind == b"tEXt":
            nul = chunk_data.find(b"\x00")
            if nul > 0:
                keyword = chunk_data[:nul]
                if keyword == b"navi-mesh-card":
                    (crc_stored,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
                    if binascii.crc32(kind + chunk_data) & 0xFFFFFFFF != crc_stored:
                        return None, MESH_CARD_PNG_DAMAGED
                    payload = chunk_data[nul + 1:]
                elif keyword == b"navi-chip":
                    saw_chip = True
        if kind == b"IEND":
            break
        pos += 8 + length + 4
    if payload is None:
        if saw_chip:
            return None, MESH_CARD_PNG_IS_CHIP
        return None, MESH_CARD_PNG_NO_PAYLOAD
    try:
        text = payload.decode("utf-8")
        card = json.loads(text)
    except Exception:
        return None, MESH_CARD_PNG_DAMAGED
    if not isinstance(card, dict):
        return None, MESH_CARD_PNG_DAMAGED
    if card.get("meshCard") != 1:
        if "meshCard" in card:
            return None, MESH_CARD_PNG_NEWER
        return None, MESH_CARD_PNG_DAMAGED
    peer, _perr = mesh_parse_card(text)
    if peer is None:
        return None, MESH_CARD_PNG_DAMAGED
    return peer, ""


# -- The ledger (spec section 6) ------------------------------------
# Metadata only, forever: who, which direction, how long, how it
# ended. Never prompt text, never reply text — a diff that
# persists content on the lender is a wrong diff (spec section 7).

def mesh_ledger_append(entry):
    try:
        if not mesh_settings(load_config())["ledger"]:
            return
        os.makedirs(MESH_DIR, exist_ok=True)
        line = {"ts": int(time.time())}
        line.update(entry)
        with open(MESH_LEDGER_PATH, "a") as f:
            f.write(json.dumps(line) + "\n")
    except Exception:
        pass


def mesh_ledger_read():
    rows = []
    try:
        with open(MESH_LEDGER_PATH) as f:
            for line in f:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except Exception:
        pass
    return rows


def mesh_balances():
    # nodeId -> lent/borrowed seconds + last activity, from the
    # ledger. Balances are a record, never a gate (Ring 1 has no
    # give-to-get enforcement).
    out = {}
    for r in mesh_ledger_read():
        peer = str(r.get("peer") or "")
        if not peer:
            continue
        b = out.setdefault(peer, {"lentSec": 0.0, "borrowedSec": 0.0, "lastTs": 0})
        sec = (r.get("wallMs") or 0) / 1000.0
        if r.get("direction") == "lent":
            b["lentSec"] += sec
        elif r.get("direction") == "borrowed":
            b["borrowedSec"] += sec
        if (r.get("ts") or 0) > b["lastTs"]:
            b["lastTs"] = r.get("ts") or 0
    return out


def mesh_hour_window(peer_id):
    # The rolling hour the caps read: borrowed-generation counts
    # and wall seconds, total and for one peer.
    cutoff = time.time() - 3600
    total = 0
    per_peer = 0
    wall = 0.0
    for r in mesh_ledger_read():
        if r.get("direction") != "lent" or (r.get("ts") or 0) < cutoff:
            continue
        total += 1
        wall += (r.get("wallMs") or 0) / 1000.0
        if r.get("peer") == peer_id:
            per_peer += 1
    return {"total": total, "perPeer": per_peer, "wallSec": wall}


def mesh_idle_seconds():
    # Seconds since this machine last finished generating (local
    # or borrowed). A machine that has never generated is idle.
    last = max(MESH_STATE["last_local_done"], MESH_STATE["last_borrowed_done"])
    if last <= 0:
        return 10 ** 9
    return time.time() - last


def mesh_busy():
    return MESH_STATE["borrowed_conn"] is not None or MESH_STATE["local_gen"] > 0


# -- Lender: the borrowed generation --------------------------------
# The lender's own llamafile answers, through the same request
# shape llamafile_chat builds — the lender adds nothing to the
# prompt. The one difference is the connection: it is registered
# in MESH_STATE so instant-off can close it mid-generation (R4).

def mesh_lender_generate(messages, endpoint, model):
    name = served_model(endpoint) or model
    body = json.dumps({
        "model": name,
        "messages": messages,
        "stream": False,
        "max_tokens": CHAT_MAX_TOKENS,
    }).encode()
    u = urllib.parse.urlparse(endpoint.rstrip("/") + "/chat/completions")
    if u.scheme == "https":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=CHAT_TIMEOUT, context=ctx)
    else:
        conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=CHAT_TIMEOUT)
    with MESH_LOCK:
        MESH_STATE["borrowed_conn"] = conn
        MESH_STATE["borrowed_started"] = time.time()
    try:
        conn.request("POST", u.path or "/", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        with MESH_LOCK:
            MESH_STATE["borrowed_resp"] = resp
        raw = resp.read()
        if resp.status != 200:
            raise RuntimeError("the llamafile server rejected the borrowed request (HTTP " + str(resp.status) + ")")
        data = json.loads(raw.decode())
        content = data["choices"][0]["message"]["content"]
        if not (content or "").strip():
            raise RuntimeError("the llamafile server answered the borrowed request with an empty reply")
        return content, data.get("usage")
    finally:
        with MESH_LOCK:
            if MESH_STATE["borrowed_conn"] is conn:
                MESH_STATE["borrowed_conn"] = None
                MESH_STATE["borrowed_peer"] = ""
                MESH_STATE["borrowed_resp"] = None
            MESH_STATE["last_borrowed_done"] = time.time()
        try:
            conn.close()
        except Exception:
            pass


def mesh_handle_status(handler, body):
    # GET /mesh/status — signed, peer-authenticated. The borrower's
    # heartbeat and pick signal: is this node lending, is it busy,
    # is it idle.
    peer = mesh_authenticate(handler, body or b"", "")
    if peer is None:
        return 401, {"ok": False, "reason": "unauthorized"}
    cfg = load_config()
    ms = mesh_settings(cfg)
    return 200, {
        "ok": True,
        "lending": bool(ms["enabled"] and ms["lend"]["enabled"]),
        "busy": mesh_busy(),
        "idle": mesh_idle_seconds() >= ms["lend"]["idleAfterSeconds"],
        "model": "navi",
        "capabilities": mesh_capabilities(cfg),
    }


def mesh_handle_borrow(handler, body):
    # POST /mesh/borrow — admission in the spec's order, then the
    # lender's own model answers the exact messages it was sent.
    # Returns (status, payload); the special status "drop" means:
    # close the borrower's connection without answering — the
    # lender was stopped mid-generation, and the borrower's
    # fusion fallback (R3) is the honest response to that.
    try:
        data = json.loads((body or b"").decode("utf-8", "replace"))
    except Exception:
        return 400, {"ok": False, "reason": "bad-request"}
    if not isinstance(data, dict):
        return 400, {"ok": False, "reason": "bad-request"}
    request_id = str(data.get("requestId") or "")
    cfg = load_config()
    ms = mesh_settings(cfg)
    if not ms["enabled"] or not ms["lend"]["enabled"]:
        return 200, {"ok": False, "reason": "lending-off"}
    peer = mesh_authenticate(handler, body, request_id)
    if peer is None:
        return 401, {"ok": False, "reason": "unauthorized"}
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return 400, {"ok": False, "reason": "bad-request"}
    # Too large is refused whole, never truncated: the assembled
    # prompt must fit the lender's own context setting.
    ctx_limit = 4096
    try:
        ctx_limit = int((cfg.get("runtime") or {}).get("ctx_size") or 4096)
    except Exception:
        pass
    est_tokens = 0
    for m in messages:
        if isinstance(m, dict):
            est_tokens += len(str(m.get("content") or "")) // 4 + 4
    if est_tokens > ctx_limit:
        return 200, {"ok": False, "reason": "too-large"}
    lend = ms["lend"]
    with MESH_LOCK:
        in_flight = MESH_STATE["borrowed_conn"] is not None
        local_running = MESH_STATE["local_gen"] > 0
    if in_flight and MESH_STATE["borrowed_peer"] == peer["nodeId"]:
        return 200, {"ok": False, "reason": "busy"}
    window = mesh_hour_window(peer["nodeId"])
    if window["total"] >= lend["maxGenerationsPerHour"] or window["perPeer"] >= lend["perPeerPerHour"]:
        return 200, {"ok": False, "reason": "cap"}
    if window["wallSec"] >= (lend["maxSharePercent"] / 100.0) * 3600:
        return 200, {"ok": False, "reason": "cap"}
    if lend["idleOnly"] and mesh_idle_seconds() < lend["idleAfterSeconds"]:
        return 200, {"ok": False, "reason": "idle"}
    if in_flight or local_running:
        # One borrowed generation at a time, and local work always
        # wins admission (Q6: a local arrival never kills a running
        # borrowed generation — it just takes the next slot).
        return 200, {"ok": False, "reason": "busy"}
    endpoint = cfg.get("live", {}).get("llamafile_endpoint", "http://localhost:8080/v1")
    model = cfg.get("live", {}).get("model_name") or "navi"
    with MESH_LOCK:
        MESH_STATE["borrowed_peer"] = peer["nodeId"]
    stop_stamp = MESH_STATE["lend_stop_stamp"]
    started = time.time()
    try:
        reply, usage = mesh_lender_generate(messages, endpoint, model)
    except Exception:
        wall_ms = int((time.time() - started) * 1000)
        if MESH_STATE["lend_stop_stamp"] != stop_stamp:
            # Instant-off landed mid-generation (R4): the ledger
            # records the abort, and the borrower's connection
            # drops so its fusion fallback (R3) speaks.
            mesh_ledger_append({"peer": peer["nodeId"], "direction": "lent", "wallMs": wall_ms, "outcome": "aborted"})
            return "drop", None
        mesh_ledger_append({"peer": peer["nodeId"], "direction": "lent", "wallMs": wall_ms, "outcome": "error"})
        return 502, {"ok": False, "reason": "lender-error"}
    if MESH_STATE["lend_stop_stamp"] != stop_stamp:
        # Build .86 (gate 4): instant-off landed while the
        # generation was completing — the reply is NOT served.
        # The ledger records the abort and the borrower's
        # connection drops, so its fusion fallback (R3) speaks
        # instead of a reply the operator already revoked.
        wall_ms = int((time.time() - started) * 1000)
        mesh_ledger_append({"peer": peer["nodeId"], "direction": "lent", "wallMs": wall_ms, "outcome": "aborted"})
        return "drop", None
    wall_ms = int((time.time() - started) * 1000)
    entry = {"peer": peer["nodeId"], "direction": "lent", "wallMs": wall_ms, "outcome": "ok"}
    if isinstance(usage, dict):
        if usage.get("prompt_tokens") is not None:
            entry["promptTokens"] = usage.get("prompt_tokens")
        if usage.get("completion_tokens") is not None:
            entry["completionTokens"] = usage.get("completion_tokens")
    mesh_ledger_append(entry)
    payload = {"ok": True, "reply": reply, "wallMs": wall_ms}
    if isinstance(usage, dict):
        payload["usage"] = usage
    return 200, payload


def mesh_stop_lending(via_dhd=False):
    # Instant-off (R4): flips lend.enabled off in the persisted
    # config and aborts any in-flight borrowed generation NOW by
    # shutting down its connection's socket (build .86, gate 4).
    # Returns the new Mesh state payload. Build 6 (#86): the
    # caller's via_dhd rides through so the returned payload
    # carries the same viaDhd field as the other Mesh answers.
    cfg = load_config()
    block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
    block = dict(block)
    lend = block.get("lend") if isinstance(block.get("lend"), dict) else {}
    lend = dict(lend)
    lend["enabled"] = False
    block["lend"] = lend
    cfg["mesh"] = block
    save_config(cfg)
    with MESH_LOCK:
        MESH_STATE["lend_stop_stamp"] = time.time()
        conn = MESH_STATE["borrowed_conn"]
        resp = MESH_STATE["borrowed_resp"]
    if conn is not None:
        # Build .86 (gate 4): close() alone does NOT interrupt the
        # lender thread blocked in resp.read() — the socket must be
        # SHUT DOWN so the in-flight read dies, and the tracked
        # response closed with it. Only then is "Stop lending now
        # aborts even a borrowed generation mid-flight" true.
        try:
            sock = getattr(conn, "sock", None)
            if sock is not None:
                sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass
    return mesh_status_payload(load_config(), via_dhd)


# -- Borrower transport ----------------------------------------------
# TLS with verification OFF and the peer card's fingerprint PINNED:
# the borrower compares the presented certificate's DER hash
# against the card by hand and refuses a mismatch in plain words.
# The pin is the authentication; no CA is involved (spec 4.1).

class _MeshFpError(Exception):
    pass


class _MeshDropped(Exception):
    pass


class _MeshUnreachable(Exception):
    pass


# Build .87 (gate 4, borrower half): the generous cap on a borrow
# read, in seconds. Connection TERMINATION is the drop signal — a
# lender that stops mid-generation hard-closes its socket and this
# borrower's blocked read fails at once (see _mesh_request). This
# cap is only the backstop for a lender that vanishes WITHOUT
# closing (a dead network path, a frozen process): far beyond a
# healthy generation's normal span, far short of the 600s chat
# timeout, and its expiry is classified exactly like termination —
# dropped, so the fusion fallback runs.
MESH_BORROW_READ_CAP = 330


def _mesh_request(peer, method, path, body, request_id, timeout):
    # One signed Mesh request, trying the peer's addresses in card
    # order. Returns (status, raw-body). Raises _MeshFpError when
    # an address answered but none presented the pinned
    # fingerprint, _MeshDropped when a connected request died
    # mid-flight, _MeshUnreachable when no address could be
    # connected at all.
    last_err = None
    fp_err = None
    for address in peer["addresses"]:
        host = str(address).split("://")[-1].split("/")[0]
        conn = None
        sent = False
        try:
            ctx = ssl._create_unverified_context()
            conn = http.client.HTTPSConnection(host, peer["port"], timeout=timeout, context=ctx)
            conn.connect()
            der = b""
            try:
                der = conn.sock.getpeercert(binary_form=True) or b""
            except Exception:
                der = b""
            fp = hashlib.sha256(der).hexdigest() if der else ""
            if peer["certFingerprint"] and fp != peer["certFingerprint"]:
                conn.close()
                # Build 7 (#87): a mismatch at ONE address no
                # longer aborts the whole request. A card can
                # carry several addresses and something else may
                # be answering at the wrong one — record the
                # mismatch and try the next address. _MeshFpError
                # is raised only at the end, when no address both
                # connected AND matched (see below).
                fp_err = "fingerprint mismatch"
                last_err = _MeshFpError("fingerprint mismatch")
                continue
            headers = mesh_signed_headers(request_id, body or b"")
            conn.request(method, path, body=body, headers=headers)
            sent = True
            if path == "/mesh/borrow":
                # Build .87 (gate 4, borrower half): bound the
                # borrow read by MESH_BORROW_READ_CAP (see its
                # comment). When the lender terminates the
                # connection mid-borrow — the drop path's socket
                # shutdown — getresponse()/read() below raises at
                # once (RemoteDisconnected / reset / EOF), and the
                # sent-branch of the except maps ANY such failure,
                # cap expiry included, to _MeshDropped. No short
                # timeout is imposed: a healthy lender generation
                # may legitimately take minutes.
                try:
                    if conn.sock is not None:
                        conn.sock.settimeout(min(timeout, MESH_BORROW_READ_CAP))
                except Exception:
                    pass
            resp = conn.getresponse()
            raw = resp.read()
            status = resp.status
            conn.close()
            return status, raw
        except _MeshFpError:
            raise
        except Exception as e:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            if sent:
                raise _MeshDropped(str(e))
            last_err = e
            continue
    # Build 7 (#87): something DID answer at one of the addresses
    # but never with the pinned certificate — that is the honest,
    # diagnosable failure, and it outranks a plain unreachable.
    if fp_err is not None:
        raise _MeshFpError(fp_err)
    raise _MeshUnreachable(str(last_err))


def mesh_probe_peer(peer, force=False):
    # GET /mesh/status with a short timeout, cached briefly.
    # Returns (status-dict-or-None, error-kind).
    cache = MESH_STATE["probe_cache"].get(peer["nodeId"])
    now = time.time()
    if not force and cache and now - cache[0] < 20:
        return cache[1], cache[2]
    status = None
    err = "unreachable"
    try:
        code, raw = _mesh_request(peer, "GET", "/mesh/status", b"", "", 3)
        if code == 200:
            try:
                parsed = json.loads(raw.decode())
                if isinstance(parsed, dict) and parsed.get("ok"):
                    status = parsed
            except Exception:
                status = None
        elif code in (401, 403):
            err = "unauthorized"
    except _MeshFpError:
        err = "fingerprint"
    except Exception:
        err = "unreachable"
    # Build 7 gate repair: the cache carries a fourth element —
    # the stamp the roster's "(last checked … ago)" age is
    # measured from. A successful probe stamps it with now; a
    # FAILED probe keeps the previous stamp, updating only the
    # error kind, so during a long outage the age keeps growing
    # (how long the peer has been dark) instead of cycling with
    # the ~30s health cadence. A peer that has never been
    # reached has no success to keep: its first failed probe
    # stamps it, and the age counts from that first check. The
    # first element stays the latest ATTEMPT's time — the 20s
    # borrow-cache freshness reads exactly what it read before.
    if status is not None:
        ok_stamp = now
    elif cache is not None and len(cache) > 3 and cache[3]:
        ok_stamp = cache[3]
    else:
        ok_stamp = now
    MESH_STATE["probe_cache"][peer["nodeId"]] = (now, status, "" if status is not None else err, ok_stamp)
    return status, "" if status is not None else err


# -- Background peer health (Build 7, #87) ---------------------------
# Before this build the probe above had exactly one caller — a
# chat borrow — so a paired peer's state existed only as a side
# effect of borrowing, and a pure lender (or a pair nobody had
# chatted across yet) sat at "not checked yet" forever, which the
# first field pair did. The bridge now watches its peers itself:
# a daemon thread probes each paired peer on a ~30s cadence while
# Mesh is enabled, and pairing / Mesh enable probe at once. Only
# state TRANSITIONS earn a log line, with the error kind — the
# log records that a peer went dark or came back, never a
# drumbeat of successful checks. Peer names only in those lines,
# never an address, like every Mesh surface.

def mesh_probe_tracked(peer):
    # One forced probe whose result is compared with the last
    # health state the bridge logged for the peer; a change is
    # written to the bridge log, anything else stays silent.
    status, err = mesh_probe_peer(peer, force=True)
    cur = "reachable" if status is not None else "unreachable:" + (err or "unreachable")
    with MESH_LOCK:
        prev = MESH_STATE["peer_health"].get(peer["nodeId"])
        if prev != cur:
            MESH_STATE["peer_health"][peer["nodeId"]] = cur
    if prev == cur:
        return status, err
    name = peer["name"]
    if status is not None:
        if prev is None:
            print("Navi Mesh: peer " + name + " checked \u2014 reachable.", flush=True)
        else:
            print("Navi Mesh: peer " + name + " is reachable again.", flush=True)
    else:
        kind = err or "unreachable"
        if prev is None:
            print("Navi Mesh: peer " + name + " checked \u2014 unreachable (" + kind + ").", flush=True)
        elif prev == "reachable":
            print("Navi Mesh: peer " + name + " is now unreachable (" + kind + ").", flush=True)
        else:
            print("Navi Mesh: peer " + name + " is still unreachable \u2014 the reason is now " + kind + ".", flush=True)
    return status, err


def mesh_probe_all_tracked():
    # Probe every paired peer once (tracked). A no-op while Mesh
    # is off — pairing can be recorded with the master switch in
    # any state, and a disabled Mesh probes nothing.
    cfg = load_config()
    ms = mesh_settings(cfg)
    if not ms["enabled"]:
        return
    for peer in ms["borrow"]["peers"]:
        try:
            mesh_probe_tracked(peer)
        except Exception:
            pass


def mesh_probe_peers_soon():
    # An immediate background probe of every paired peer: pairing
    # and Mesh enable call this so a fresh peer is checked at
    # once instead of waiting for the health cadence. Never
    # blocks the caller — the probes run on their own thread.
    t = threading.Thread(target=mesh_probe_all_tracked, daemon=True)
    t.start()


def mesh_health_loop():
    # The cadence itself. The loop runs for the bridge's life
    # once started and simply idles — no probes, no log — while
    # Mesh is off or nothing is paired.
    while True:
        try:
            mesh_probe_all_tracked()
        except Exception:
            pass
        time.sleep(30)


def mesh_ensure_health_thread():
    with MESH_LOCK:
        if MESH_STATE["health_started"]:
            return
        MESH_STATE["health_started"] = True
    t = threading.Thread(target=mesh_health_loop, daemon=True)
    t.start()


def _mesh_borrow_once(peer, messages):
    # A single borrow attempt against a peer already probed
    # reachable. Outcomes: ("ok", reply, wallMs), ("refusal",
    # reason), ("dropped", None) for an in-flight failure (R3),
    # ("error", kind) for a failure before admission.
    request_id = secrets.token_hex(8)
    body = json.dumps({
        "requestId": request_id,
        "messages": messages,
        "model": "navi",
        "maxTokens": CHAT_MAX_TOKENS,
    }).encode()
    started = time.time()
    try:
        code, raw = _mesh_request(peer, "POST", "/mesh/borrow", body, request_id, CHAT_TIMEOUT)
    except _MeshFpError:
        return ("error", "fingerprint")
    except _MeshDropped:
        # Build .87: remember the drop for the status payload —
        # the Servers row's Mesh warning ("<name> dropped") reads
        # it until a later probe finds the peer healthy again.
        with MESH_LOCK:
            MESH_STATE["peer_dropped"][peer["nodeId"]] = time.time()
        return ("dropped", None)
    except _MeshUnreachable:
        return ("error", "unreachable")
    except Exception:
        return ("error", "unreachable")
    if code in (401, 403):
        return ("refusal", "unauthorized")
    try:
        data = json.loads(raw.decode())
    except Exception:
        with MESH_LOCK:
            MESH_STATE["peer_dropped"][peer["nodeId"]] = time.time()
        return ("dropped", None)
    if code == 200 and isinstance(data, dict) and data.get("ok"):
        wall = data.get("wallMs")
        if not isinstance(wall, (int, float)):
            wall = int((time.time() - started) * 1000)
        return ("ok", str(data.get("reply") or ""), int(wall))
    reason = str((data or {}).get("reason") or "lender-error") if isinstance(data, dict) else "lender-error"
    return ("refusal", reason)


def mesh_try_borrow(messages, cfg, ms):
    # The borrower (spec section 2): first reachable peer only —
    # Ring 1 never races lenders. Returns (reply, mesh-payload) on
    # a mesh-served answer, or (None, mesh-payload) describing the
    # local fallback the caller is about to run. (None, None) when
    # Mesh does not apply at all.
    peers = ms["borrow"]["peers"]
    if not peers:
        return None, None
    if not mesh_node_id():
        ok, _err = mesh_ensure_identity(cfg)
        if not ok:
            return None, None
    with MESH_LOCK:
        MESH_STATE["borrow_out"] = True
    try:
        last_reason = "unreachable"
        for peer in peers:
            # Build 7 (#87): canBorrow is enforced HERE, on the
            # borrowing side — this machine does not borrow from
            # a peer whose flag is off. It no longer gates the
            # lender's authentication (see mesh_authenticate):
            # pairing is that side's consent.
            if not peer["canBorrow"]:
                continue
            status, err = mesh_probe_peer(peer)
            if status is None and err == "unreachable":
                # Build 7 gate repair (close-out): the answer above
                # may be the 20s probe cache holding a FAILED probe —
                # since Build 7 the background health thread keeps
                # that cache permanently warm, so a lender killed
                # mid-generation (the drop path) leaves a fresh
                # failure cached, and the very borrow meant to
                # discover the drop read the cache and never
                # attempted the request at all: no drop recorded,
                # no fusion notice, reason "unreachable" — the
                # fusion path starved exactly like the idle path
                # did. A cached FAILURE earns one fresh probe
                # before the borrow gives up on this peer; only a
                # fresh failure keeps "unreachable". A genuinely
                # down lender pays one extra short probe. Mirrors
                # the not-lending fresh check below and the
                # busy/idle grace paths, which already re-probe
                # with force=True. (A cached SUCCESS is untouched:
                # freshness only ever ADDS an attempt, and a failed
                # fresh probe of a just-dropped lender still
                # classifies through _mesh_borrow_once.)
                status, err = mesh_probe_peer(peer, force=True)
            if status is None:
                # A failed probe — cached or fresh — never clears
                # a recorded drop. The drop is the freshest thing
                # this machine knows about the peer (Build 6's
                # manifest: warning "<name> dropped" read straight
                # after it), and a lender that died mid-answer is
                # exactly the peer whose next probes all fail: the
                # failure EXPLAINS the drop, it does not supersede
                # it. The status payload already weighs the two —
                # the drop stands until a probe SUCCEEDS (its
                # success stamp postdates the drop), a borrow is
                # served, or five minutes pass. (An earlier repair
                # popped the record here the moment a fresh probe
                # proved the peer dark; that raced the drop
                # discovery itself — the borrow meant to find the
                # drop could read a warm failed cache, force one
                # dark probe, and erase the record before the row
                # ever showed it.)
                last_reason = err or "unreachable"
                continue
            name = peer["name"]
            with MESH_LOCK:
                MESH_STATE["borrow_peer"] = name
            if not status.get("lending"):
                # Build 7 gate repair: the probe above may have
                # served a CACHED status (up to 20s old), and the
                # background health thread now keeps that cache
                # permanently warm — so a lender that stopped and
                # then re-enabled lending inside the cache window
                # would read as still-off and the borrow would
                # never even be attempted. Re-probe ONCE fresh
                # before refusing; only a fresh not-lending (or a
                # failed fresh probe) earns "lending-off". A
                # genuinely-off lender pays one extra short probe
                # on this path. Mirrors the busy-grace path below,
                # which already re-probes with force=True.
                fresh, _ferr = mesh_probe_peer(peer, force=True)
                if fresh is None or not fresh.get("lending"):
                    return None, {"servedBy": "local", "fellBack": True, "reason": "lending-off", "node": name}
                status = fresh
            outcome = _mesh_borrow_once(peer, messages)
            if outcome[0] == "ok":
                # Build .87: a served borrow is the freshest word
                # on the peer — it clears any recorded drop, so the
                # status row stops warning about a peer that is
                # demonstrably answering again.
                with MESH_LOCK:
                    MESH_STATE["peer_dropped"].pop(peer["nodeId"], None)
                mesh_ledger_append({"peer": peer["nodeId"], "direction": "borrowed", "wallMs": outcome[2], "outcome": "ok"})
                return outcome[1], {"servedBy": "mesh", "node": name, "fellBack": False}
            if outcome[0] == "dropped":
                # R3 FUSION: the notice is data; the caller runs a
                # FRESH local reply — two models' prose is never
                # spliced.
                return None, {
                    "servedBy": "local", "fellBack": True, "reason": "lender-dropped", "node": name,
                    "notice": name + " dropped mid-answer \u2014 this reply was generated locally instead.",
                }
            if outcome[0] == "error":
                return None, {"servedBy": "local", "fellBack": True, "reason": outcome[1], "node": name}
            reason = outcome[1]
            if reason == "idle":
                # Build 7 gate repair: "idle" is the ONE admission
                # refusal that carries a TIME dimension — the lender
                # accepts this borrow once it has been quiet for
                # idleAfterSeconds (default 60s). A borrower that
                # sends chats back-to-back right after a served
                # borrow would otherwise watch every follow-up fall
                # back locally as "idle" — the reason also renders
                # in the chat notice as "is not idle yet" — which is
                # indistinguishable in the payload from the request
                # never having been attempted, and it starves the
                # in-flight fusion path entirely (a borrow refused
                # here never registers on the lender). It gets the
                # busy shape, not the busy word: poll the lender's
                # probe-reported idle state for up to graceMs and
                # retry admission ONCE the moment the lender itself
                # reports idle; a refused retry keeps reason
                # "idle", and a mid-generation lender still
                # classifies through the busy/drop paths below and
                # in _mesh_borrow_once. Deliberately NO unbounded
                # wait: a lender idle only after the grace is spent
                # serves the NEXT request, exactly like busy (R5).
                deadline = time.time() + max(0, ms["borrow"]["graceMs"]) / 1000.0
                while time.time() < deadline:
                    time.sleep(0.4)
                    st2, _e2 = mesh_probe_peer(peer, force=True)
                    if st2 is not None and st2.get("idle"):
                        outcome = _mesh_borrow_once(peer, messages)
                        if outcome[0] == "ok":
                            with MESH_LOCK:
                                MESH_STATE["peer_dropped"].pop(peer["nodeId"], None)
                            mesh_ledger_append({"peer": peer["nodeId"], "direction": "borrowed", "wallMs": outcome[2], "outcome": "ok"})
                            return outcome[1], {"servedBy": "mesh", "node": name, "fellBack": False}
                        if outcome[0] == "dropped":
                            return None, {
                                "servedBy": "local", "fellBack": True, "reason": "lender-dropped", "node": name,
                                "notice": name + " dropped mid-answer \u2014 this reply was generated locally instead.",
                            }
                        if outcome[0] == "error":
                            return None, {"servedBy": "local", "fellBack": True, "reason": outcome[1], "node": name}
                        reason = outcome[1]
                        break
                return None, {"servedBy": "local", "fellBack": True, "reason": reason, "node": name}
            if reason == "busy":
                # R5 GRACE: poll/retry admission for up to graceMs.
                # Once local generation starts (grace spent), the
                # lender is never claimed mid-reply — it serves the
                # NEXT request.
                deadline = time.time() + max(0, ms["borrow"]["graceMs"]) / 1000.0
                while time.time() < deadline:
                    time.sleep(0.4)
                    st2, _e2 = mesh_probe_peer(peer, force=True)
                    if st2 is not None and not st2.get("busy"):
                        outcome = _mesh_borrow_once(peer, messages)
                        if outcome[0] == "ok":
                            with MESH_LOCK:
                                MESH_STATE["peer_dropped"].pop(peer["nodeId"], None)
                            mesh_ledger_append({"peer": peer["nodeId"], "direction": "borrowed", "wallMs": outcome[2], "outcome": "ok"})
                            return outcome[1], {"servedBy": "mesh", "node": name, "fellBack": False}
                        break
                return None, {"servedBy": "local", "fellBack": True, "reason": "busy", "node": name}
            return None, {"servedBy": "local", "fellBack": True, "reason": reason, "node": name}
        return None, {"servedBy": "local", "fellBack": True, "reason": last_reason}
    finally:
        with MESH_LOCK:
            MESH_STATE["borrow_out"] = False
            MESH_STATE["borrow_peer"] = ""


def mesh_status_payload(cfg, via_dhd=False):
    # The /api/status mesh section and the Settings card's state:
    # metadata only — state, peers, balances. No content, ever.
    # Build .87: the payload also carries the status column's
    # at-a-glance verdict — a summary "state" + short "warning"
    # string, and per peer a "status" word + "lastProbeError" —
    # all read from state the bridge already tracks (the probe
    # cache, the recorded drops, the lend/borrow flags). Names and
    # state words only: a peer's addresses never enter this
    # payload, exactly as they never render anywhere.
    # Build 6 (#86): "viaDhd" says whether THE REQUEST this
    # payload answers arrived through the DHD proxy surface (the
    # X-Apex-Via: dhd header the proxy stamps). It is a property
    # of the request, not of the machine, so the callers that
    # answer an operator's view pass it in; everyone else gets
    # False. The dashboard reads it to render the Lend switch
    # locked on the remote view — the in-person turn-on lock
    # itself is enforced at the settings handler, unchanged.
    ms = mesh_settings(cfg)
    balances = mesh_balances()
    peers = []
    now = time.time()
    for p in ms["borrow"]["peers"]:
        b = balances.get(p["nodeId"], {"lentSec": 0.0, "borrowedSec": 0.0, "lastTs": 0})
        cache = MESH_STATE["probe_cache"].get(p["nodeId"])
        reachable = None
        probe = None
        probe_err = ""
        probe_stamp = 0.0
        probe_age = None
        if cache:
            # Build 7 (#87): the last probe's word is DURABLE —
            # it no longer expires after 60s. A failed check
            # stays "unreachable", with its error kind and its
            # age, until a newer probe replaces it; reachable is
            # None (the roster's "not checked yet") only when no
            # probe has ever completed for this peer. Freshness
            # now comes from the background health cadence, not
            # from forgetting.
            reachable = cache[1] is not None
            probe = cache[1] if isinstance(cache[1], dict) else None
            probe_err = str(cache[2] or "")
            probe_stamp = cache[0]
            # The age reads the cache's fourth element — the
            # last SUCCESSFUL probe's stamp (the first failed
            # probe's, for a peer never reached) — never the
            # latest attempt's, so it grows through an outage.
            probe_age = max(0, int(now - (cache[3] if len(cache) > 3 and cache[3] else cache[0])))
        caps = p.get("capabilities")
        if probe is not None and probe.get("capabilities"):
            live_caps = _mesh_caps_sanitize(probe.get("capabilities"))
            if live_caps is not None:
                caps = live_caps
        # The peer's one-word state: a recorded drop that no later
        # healthy probe has superseded outranks the probe cache —
        # it is the freshest thing this machine knows about the
        # peer, and it is exactly what the operator needs warned
        # about. Drops age out after five minutes so a stale one
        # cannot haunt the row forever. Build 7 gate repair: the
        # superseding stamp is the last SUCCESSFUL probe's (the
        # cache's fourth element), never the latest ATTEMPT's —
        # a failed health probe landing after a drop (the lender
        # is down; every cadence tick fails) advanced the attempt
        # stamp past the drop and flipped the row's warning from
        # "<name> dropped" to "<name> unreachable", hiding the
        # drop behind the outage it caused. A peer that ANSWERS
        # again still supersedes the drop at once, exactly as
        # before; a peer that merely gets probed and fails does
        # not.
        drop_stamp = MESH_STATE["peer_dropped"].get(p["nodeId"], 0.0)
        ok_stamp = cache[3] if cache and len(cache) > 3 and cache[3] else 0.0
        if drop_stamp and now - drop_stamp < 300 and drop_stamp >= ok_stamp:
            peer_status = "dropped"
        elif reachable is True:
            peer_status = "reachable"
        elif reachable is False:
            peer_status = "unreachable"
        else:
            peer_status = "unknown"
        peers.append({
            "name": p["name"],
            "nodeId": p["nodeId"],
            "short": p["nodeId"][:12],
            "canBorrow": p["canBorrow"],
            "reachable": reachable,
            "status": peer_status,
            "lastProbeError": probe_err if reachable is False else "",
            # Build 7 (#87): seconds since the peer was last
            # successfully checked — or since its first check
            # when it has never been reached — or null when it
            # has never been probed at all. The roster renders
            # "(last checked 42s ago)" from it beside a failed
            # state, and through an outage it keeps growing:
            # failed attempts refresh the reason, not the age.
            "lastProbeAgeSec": probe_age,
            "balanceSec": round(b["lentSec"] - b["borrowedSec"], 1),
            "lastTs": b["lastTs"],
            "capabilities": caps,
            "probeLending": (bool(probe.get("lending")) if probe is not None else None),
            "probeBusy": (bool(probe.get("busy")) if probe is not None else None),
            "probeIdle": (bool(probe.get("idle")) if probe is not None else None),
        })
    # The summary the Servers row renders (build .87): one state
    # word for the dot, one SHORT warning for the label — the
    # first problem peer by name, never an address.
    state = "off"
    warning = ""
    if ms["enabled"]:
        dropped_peer = next((p for p in peers if p["status"] == "dropped"), None)
        unreach_peer = next((p for p in peers if p["status"] == "unreachable"), None)
        if not peers:
            state = "no-peers"
        elif dropped_peer is not None:
            state = "warning"
            warning = str(dropped_peer["name"]) + " dropped"
        elif unreach_peer is not None:
            state = "warning"
            warning = str(unreach_peer["name"]) + " unreachable"
        elif MESH_STATE["borrow_out"]:
            state = "borrowing"
        elif MESH_STATE["borrowed_conn"] is not None:
            state = "lending"
        elif any(p["status"] == "reachable" for p in peers):
            state = "reachable"
        else:
            state = "on"
    return {
        "enabled": ms["enabled"],
        "role": ms["role"],
        "nodeName": ms["nodeName"],
        "nodeId": mesh_node_id() or ms["nodeId"],
        "borrowEnabled": ms["borrow"]["enabled"],
        "graceMs": ms["borrow"]["graceMs"],
        "lendEnabled": ms["lend"]["enabled"],
        "lend": ms["lend"],
        "ledgerInBackup": ms["ledgerInBackup"],
        "borrowing": bool(MESH_STATE["borrow_out"]),
        "lendingNow": MESH_STATE["borrowed_conn"] is not None,
        "state": state,
        "warning": warning,
        "viaDhd": bool(via_dhd),
        "capabilities": mesh_capabilities(cfg),
        "peers": peers,
    }


# -- The dedicated Mesh door -----------------------------------------
# Mesh ALWAYS listens on its own TLS port (build .86) — its own
# door, its own certificate, in every configuration. The DHD proxy
# refuses /mesh/* outright and the dashboard surface does not
# serve the node-facing endpoints at all: borrowers dial this
# port — the peer card's port — only. There is no plaintext Mesh
# listener.

class MeshHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length > 0 else b""

    def do_GET(self):
        if self.path.split("?")[0] == "/mesh/status":
            code, payload = mesh_handle_status(self, b"")
            self._send(code, payload)
        else:
            self._send(404, {"ok": False, "reason": "not-found"})

    def do_POST(self):
        if self.path.split("?")[0] == "/mesh/borrow":
            code, payload = mesh_handle_borrow(self, self._body())
            if code == "drop":
                # Build .87 (gate 4, borrower half): a handler-level
                # connection.close() on this HTTP/1.1 keep-alive TLS
                # connection does NOT deliver a prompt EOF to a
                # borrower blocked in getresponse() — the borrow
                # strands for minutes instead of completing. Hard-
                # close at the SOCKET level: shutdown(SHUT_RDWR)
                # first, so the termination lands on the wire at
                # once, then close. The borrower reads termination
                # as the drop signal and its fusion fallback speaks.
                self.close_connection = True
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.connection.close()
                except Exception:
                    pass
                return
            self._send(code, payload)
        else:
            self._send(404, {"ok": False, "reason": "not-found"})


def mesh_start_listener():
    global MESH_SERVERS
    # Build 7 (#87): the peer health thread starts with the Mesh
    # door — at boot and at enable alike (this is the one place
    # both paths meet). It idles while Mesh is off or unpaired.
    mesh_ensure_health_thread()
    if MESH_SERVERS:
        return
    cfg = load_config()
    ms = mesh_settings(cfg)
    if not ms["enabled"]:
        return
    ok, _err = mesh_ensure_cert()
    if not ok:
        return
    cert_path, key_path = mesh_active_cert()
    try:
        server = ThreadingHTTPServer(("0.0.0.0", ms["port"]), MeshHandler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert_path, key_path)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        MESH_SERVERS = [server]
    except Exception:
        MESH_SERVERS = []


def mesh_stop_listener():
    global MESH_SERVERS
    for s in MESH_SERVERS:
        try:
            s.shutdown()
        except Exception:
            pass
        try:
            s.server_close()
        except Exception:
            pass
    MESH_SERVERS = []

def read_file(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def app_version_status(cfg=None):
    # The VERSION file's optional build status: the number may be
    # followed by a status word - "0.1.8 edge" - or carry it as a
    # suffix - "0.1.8-edge". Edge and beta builds wear a
    # single-letter tag in the menu footer (e / b); a full release
    # wears none. Anything unrecognized reads as stable. When the file is
    # missing entirely, the status of the release this bridge
    # shipped in answers — never the preserved config's record,
    # which belongs to an older build (see SHIPPED_VERSION above).
    text = read_file(VERSION_PATH).strip()
    if not text:
        return SHIPPED_VERSION_STATUS
    raw = text.splitlines()[0].strip().lower()
    # The pre-release word is "edge" (build .83); "alpha" is the
    # retired word from before the sync and still reads as edge,
    # so a VERSION file written by an older build is never
    # misread as a full release.
    for word in ("edge", "beta", "alpha"):
        if raw.endswith(" " + word) or raw.endswith("-" + word):
            return "edge" if word == "alpha" else word
    return "stable"


def app_version(cfg=None):
    # The VERSION file is the source of truth (see VERSION_PATH).
    # The reported number never carries the status word — the
    # status rides separately as versionStatus, and the dashboard
    # renders the two together ("v0.1.8e" on an Edge build). When
    # the file is
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
        for word in ("edge", "alpha", "beta", "stable"):
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


def persona_prompt(cfg, operator_name="", memory_mode="autonomous"):
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
    # Memory from chat (build .81, issue #72): she may pull memories
    # out of the conversation on her own judgment, inside the same
    # reply she is already generating — no second inference pass, so
    # modest hardware pays nothing extra. The bridge strips the
    # marker lines before the reply is shown or spoken and returns
    # the saves as data; the dashboard files them and shows the
    # operator a receipt of exactly what was saved, with an Undo.
    # In trigger-only mode the instruction is not sent at all, and
    # the bridge drops any marker a reply still carries.
    if memory_mode != "trigger":
        prompt += (
            "\n\nMemory: you keep long-term memory entries for your operator. "
            "When this conversation produces something durable — a fact about "
            "them, a preference, a decision, a commitment, or a correction to "
            "something you already carry — you may save it by ending your reply "
            "with a line of exactly this form: [[remember: <the fact, stated "
            "plainly in one sentence>]]. At most two per reply, and only when "
            "it truly matters; small talk and command output are not memories. "
            "If the operator corrects a fact, save the corrected fact the same "
            "way — it replaces the old entry rather than piling up beside it. "
            "Never save secrets (passwords, keys, card numbers, tokens): a "
            "save like that is refused before it is written. The marker line "
            "is removed before the operator sees your reply, and they are "
            "shown a receipt of exactly what you saved — never mention the "
            "marker itself."
        )
    return prompt


# ---------------------------------------------------------------------
# Memory from chat (build .81, issue #72).
#
# Two doors, one store. The trigger — "remember this", "remember:
# …", "save this to your memory" — is deterministic bridge work,
# decided before the model route like DHD intents and Vault
# filing: the fact is extracted here and carried back in the
# payload, and the dashboard files it and shows the receipt. Her
# own judgment rides the model's reply: the persona prompt teaches
# her the [[remember: …]] marker, extract_memory_markers strips
# those lines from the reply before it is shown or spoken, and the
# saves travel back as payload data — never as words in her text.
# The entries themselves live with the dashboard (its local store,
# like the rest of her remembered facts); corrections are matched
# there by the same key/overlap rule memory_fact_key mirrors here.
# Secrets are screened on both doors and refused before anything
# is written, and no save is ever silent: every outcome rides the
# payload back to a receipt in the thread.

MEMORY_SECRET_RE = re.compile(r"\b(password|passcode|passwd|api[\s_-]?key|secret|token|credential|ssn|social security|credit card|card number|cvv)\b", re.I)
MEMORY_LONG_DIGITS_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
MEMORY_MARKER_RE = re.compile(r"^\s*\[\[remember:\s*(.+?)\s*\]\]\s*$", re.I | re.M)


def memory_looks_secret(text):
    return bool(MEMORY_SECRET_RE.search(text or "") or MEMORY_LONG_DIGITS_RE.search(text or ""))


def normalize_memory_fact(text):
    t = re.sub(r"\s+", " ", (text or "").strip()).strip("\"'")
    if not t:
        return ""
    t = t[0].upper() + t[1:]
    if not re.search(r"[.!?]$", t):
        t += "."
    return t


def memory_fact_key(text):
    t = (text or "").lower()
    if re.search(r"(?:operator'?s|my) name is\b", t) or re.match(r"name\s*:", t):
        return "name"
    if re.search(r"(?:operator lives|i live|i'?m based|operator'?s (?:home|hometown) is|my (?:home|hometown) is)\b", t):
        return "home"
    if re.search(r"(?:operator works|i work|my job is|operator'?s job is)\b", t):
        return "work"
    m = re.search(r"favou?rite\s+([a-z][a-z -]*?)\s+is\b", t)
    if m:
        return "favorite:" + m.group(1).strip()
    return None


def memory_trigger(text):
    # The operator's trigger. Returns ("fact", payload),
    # ("prior", None) when the ask points at the previous message
    # ("remember this" with nothing after it), or None when the
    # line is not a trigger — questions about remembering ("do you
    # remember…", "remember when…") are talk, not triggers.
    line = (text or "").strip()
    if line.startswith(">"):
        line = line[1:].strip()
    if "?" in line and re.match(r"(?i)(do|did|can|could|what|why|how|remember when)\b", line):
        return None
    m = re.match(r"(?i)(?:please\s+)?(?:navi[,\s]+)?(?:save|write|put)\s+(?:this|that)\s+(?:to|in|into)\s+(?:your\s+)?memory\s*[:\-]?\s*(.*)$", line)
    if m:
        rest = (m.group(1) or "").strip()
        return ("fact", rest) if rest else ("prior", None)
    m = re.match(r"(?i)(?:please\s+)?(?:navi[,\s]+)?remember[\s:]+(.*)$", line)
    if not m:
        return None
    rest = (m.group(1) or "").strip()
    if not rest or re.match(r"(?i)(when|me|us|the time)\b", rest):
        return None
    pm = re.match(r"(?i)(?:this|that)\b\s*[:\-—,]?\s*(.*)$", rest)
    if pm:
        rest = (pm.group(1) or "").strip()
        return ("fact", rest) if rest else ("prior", None)
    if rest[:1] in (":", "-"):
        rest = rest[1:].strip()
        return ("fact", rest) if rest else ("prior", None)
    return ("fact", rest)


def extract_memory_markers(reply, memory_mode):
    # Strip [[remember: …]] lines from a model reply. Returns
    # (clean_reply, saves, refused_count). Markers are honored
    # only when the mode lets her save on her own judgment; in
    # trigger mode they are stripped and dropped. Secret-shaped
    # saves count as refused — never written, and the dashboard's
    # receipt says so.
    saves = []
    refused = [0]

    def _take(m):
        fact = normalize_memory_fact(m.group(1))
        if not fact:
            return ""
        if memory_mode == "trigger":
            return ""
        if memory_looks_secret(fact):
            refused[0] += 1
            return ""
        saves.append({"text": fact, "origin": "autonomous", "key": memory_fact_key(fact), "proposed": memory_mode == "ask"})
        return ""

    clean = MEMORY_MARKER_RE.sub(_take, reply or "")
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean, saves[:2], refused[0]


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



def path_complete(prefix, base=None):
    """One-level completion for the chat composer (#27d). Pure helper:
    lists only the prefix's parent directory, directories first then
    files (alphabetical), at most 12 entries, dotfiles only when the
    partial name starts with a dot. Replacement text preserves the
    operator's prefix style (~ stays ~, relative stays relative); a
    directory's replacement ends with '/'."""
    prefix = prefix or ""
    slash = prefix.rfind("/")
    dirpart = prefix[:slash + 1] if slash != -1 else ""
    partial = prefix[slash + 1:] if slash != -1 else prefix
    if prefix.startswith("~"):
        expanded = os.path.expanduser(dirpart if dirpart else "~")
        listdir = expanded
    elif dirpart.startswith("/"):
        listdir = dirpart
    else:
        root = base if base is not None else shell_cwd()
        listdir = os.path.join(root, dirpart) if dirpart else root
    try:
        names = os.listdir(listdir)
    except Exception:
        return []
    dirs, files = [], []
    for nm in names:
        if nm.startswith(".") and not partial.startswith("."):
            continue
        if not nm.lower().startswith(partial.lower()):
            continue
        full = os.path.join(listdir, nm)
        try:
            is_dir = os.path.isdir(full)
        except Exception:
            is_dir = False
        (dirs if is_dir else files).append(nm)
    out = []
    for nm in sorted(dirs):
        out.append({"name": nm, "description": "Folder", "replacement": dirpart + nm + "/", "isDir": True})
    for nm in sorted(files):
        out.append({"name": nm, "description": "File", "replacement": dirpart + nm, "isDir": False})
    return out[:12]


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
# App updates — the Updater, for real (build .47; end-to-end apply
# in build .56).
#
# A check asks GitHub for the project's latest published release
# and compares its tag against the VERSION file (the very number
# app_version reports), so the footer, the status answer, and the
# Updater all read the same truth. A check that cannot complete —
# offline, or GitHub's rate limit — answers ok: False with the
# reason named. It never dresses a failure up as "up to date".
#
# Apply carries the update through from the one click (build .56):
# download the release's package zip -> verify it -> stage it
# under updates/<tag>/package -> hand the install to a detached
# helper the bridge writes into updates/<tag>/, which outlives the
# bridge, runs the staged installer itself (never --fresh: the
# installer is the one path that replaces the app, because it owns
# the state-preservation stash — chips, packs and their indexes,
# the llamafile, Soul/Memory, voice, GitHub settings — and the
# bridge cannot overwrite itself while it runs) -> relaunch the
# app through start.sh -> confirm. The helper records every step
# in config/update-result.json; the panel polls that record while
# the apply runs (downloading / verifying / staging / installing /
# restarting) and reads the outcome from it afterwards. "Updated"
# is claimed only when the install after the relaunch reads as
# the target — the VERSION file's number AND, for a same-version
# Edge refresh, the build sequence the relaunched bridge reports
# and the one baked into the bridge.py on disk (Build 4: the
# number alone is the same before and after a refresh, so a
# confirmation that read only the number once certified an
# install of the previous build as the new one). A step that did
# not observe its own success never reports one.
#
# The failure ladder is part of the design: every step can fail
# and names itself and its reason in the record (download failed,
# not a zip, not an Apex package, staging failed, the installer
# failed with its exit state, the relaunch did not answer, the
# version after relaunch is not the expected one). A failed
# validation leaves nothing staged; a failure at or after staging
# leaves the staged package in place and the record carries the
# manual fallback — the staged folder and the one install
# command — labeled as the fallback it is.
#
# Build 5 — the helper can no longer die traceless. The Build 4
# round-trip gate ran a genuine Build 3 install applying a
# package through its own Updater: the staged installer ran
# through to "Done.", and then the detached helper died without
# a trace — apply.log 0 bytes, no apply-relaunch.log ever
# created, the record frozen at working/installing, no bridge
# relaunched. Diagnosis from the helper's source: its step
# sequence after the installer exits is read the install log
# back -> record the DHD-prerequisites step -> record
# "restarting" -> spawn start.sh -> poll /api/status for up to
# five minutes -> verify (Build 4's lock: the answering bridge
# reports the target build AND bridge.py on disk carries it)
# -> finish the record. Every death in that window was
# invisible by construction: the helper printed nothing (so
# apply.log is empty BY DESIGN on any run that does not crash
# Python itself), it had no top-level guard and no signal
# handlers, write_result merged into the record with no
# freshness stamp, and the failure-path ordering called fail()
# BEFORE relaunch() — an exception inside the failure write
# itself skipped the relaunch entirely. Ranked mechanisms for
# the gate's evidence: (1) an external signal kill at the
# installer's end — the only mechanism consistent with all
# three facts at once (a Python exception would have left a
# traceback in apply.log; the log was empty; a mere hang would
# have left a live process). The helper runs in its own
# session but in the same process tree and user-service world
# as everything the installer stops and restarts at exactly
# that moment — pattern kills, the pid-file kill, the shell
# stop, service manipulation — and SIGTERM/SIGKILL leave no
# trace in the victim. (2) An uncaught exception in the
# unguarded post-installer segment (record writes against a
# config tree the installer had just replaced/re-owned) —
# real, and closed by the guard, but it predicts a traceback
# the gate did not see, so it ranks second for THIS incident.
# (3) A block inside subprocess.run past the installer's
# "Done." — indistinguishable from death in the old design,
# which is itself the indictment. The repair defends against
# all three and makes the next incident self-convicting: the
# helper keeps a step log (updates/<tag>/apply-trace.log) from
# its first instruction — step boundaries, the installer's
# exit, the relaunch spawn, the confirmation's found-vs-
# expected values, a 30-second heartbeat (a log still beating
# at one step is a block; a log whose beats stop is a kill) —
# a top-level guard records any exception into the record
# (failed + step + reason) and mirrors the traceback to
# apply.log, signal handlers record SIGTERM/SIGINT/SIGHUP the
# same way before exiting, a relaunch that cannot even spawn
# fails loudly at "restart" with found-vs-expected detail, and
# the no-answer failure names what was expected and what was
# found. For the death no in-process guard survives (SIGKILL,
# OOM, power), the bridge's apply watchdog closes a record
# whose helper pid is dead and whose last write is stale as
# failed at its last step, quoting the step log's final line —
# the record can never again freeze at working/installing.
#
# Gzip tolerance (build .56): a package asset can arrive
# gzip-wrapped (its first bytes are the gzip signature, 1f 8b,
# instead of a zip's PK) when whatever staged the release asset
# compressed the zip itself. The validator unwraps that layer
# and runs the same Apex-package verification on the zip inside;
# only when neither the raw payload nor its unwrapped form is a
# valid Apex package does it refuse, and the refusal names what
# was wrong. The plain-PK path behaves exactly as it always did.
#
# NAVI_UPDATE_FEED_URL overrides the release-feed address. It is
# the seam the project's own end-to-end updater tests use to run
# this real apply path against a local stand-in instead of the
# live release; it is unset in normal installs.

UPDATES_DIR = os.path.join(ROOT, "updates")
UPDATE_RESULT_PATH = os.path.join(ROOT, "config", "update-result.json")


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


def _status_rank(status):
    # Fuller beats preview at the same numbers: a full release
    # outranks beta, which outranks an Edge build.
    return {"stable": 2, "beta": 1, "edge": 0}.get(status, 0)


def _release_is_newer(tag, current_number, current_status, build_seq=None):
    # The Updater's real comparison (build .83): higher numbers
    # win; at the same numbers, only a graduation counts — an
    # Edge build of the numbers you already run as a full release
    # is a preview you passed, not an update, and the full
    # release of numbers you run as an Edge build IS one.
    # Build .86 adds the third tier: same numbers AND same status
    # AND the running build is an Edge publication — a candidate
    # carrying a higher Build number (build_seq) than the running
    # SHIPPED_BUILD_SEQ is a same-version refresh and IS newer; a
    # candidate with no build number, or one no higher, is NOT.
    num, status = _tag_parts(tag)
    if not num:
        return False
    a, b = _version_tuple(num), _version_tuple(current_number)
    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))
    if a != b:
        return a > b
    if _status_rank(status) != _status_rank(current_status):
        return _status_rank(status) > _status_rank(current_status)
    if current_status == "edge" and build_seq is not None:
        return build_seq > SHIPPED_BUILD_SEQ
    return False


def _release_build_seq(rel):
    # A publication's place in its own version's sequence
    # (build .86): "Build <n>" parsed from the release's name
    # first, then its body's opening lines. None when the
    # release carries no build number.
    name = str(rel.get("name") or "")
    m = re.search(r"Build ([0-9]+)", name)
    if m:
        return int(m.group(1))
    body = str(rel.get("body") or "")
    for line in body.splitlines()[:6]:
        m = re.search(r"Build ([0-9]+)", line)
        if m:
            return int(m.group(1))
    return None


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


def updater_channel_explicit(cfg=None):
    # True only when the OPERATOR picked a channel in the Updater
    # panel — the /api/settings/updater-channel save stamps
    # channelExplicit beside the choice (Build 2). A channel value
    # that arrived baked into the config by the package, or was
    # written by a build from before channels were a choice, is a
    # starting shape, not a choice, and never counts as one.
    if isinstance(cfg, dict):
        block = cfg.get("updater")
        if isinstance(block, dict):
            return block.get("channelExplicit") is True and block.get("channel") in ("stable", "edge")
    return False


def updater_channel(cfg=None):
    # The EFFECTIVE release channel this install follows (build
    # .83; the default rule repaired in Build 2). An explicit
    # operator choice wins, exactly as saved. With no explicit
    # choice, the running build's own line is the default: an
    # Edge build follows Edge — a config that predates channels
    # carries a baked "stable" it never chose, and honoring it
    # stranded Edge installs on a channel that never publishes
    # their builds (the Build 2 field report: an Edge install
    # told it was up to date against Stable's v0.1.7). A Stable
    # build's default stays "stable" — the safe channel is the
    # default for the line that has one, never silently Edge.
    if updater_channel_explicit(cfg):
        return cfg["updater"]["channel"]
    if app_version_status(cfg) == "edge":
        return "edge"
    return "stable"


def _shape_release(rel):
    # One GitHub release record in the Updater's shape. The
    # package asset is the release's .zip (the export package);
    # a release without one can be reported but never staged.
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
        "notes": str(rel.get("body") or "").replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10)),
        "prerelease": bool(rel.get("prerelease")),
        "buildSeq": _release_build_seq(rel),
        "asset": asset,
    }


def latest_release(channel="stable"):
    # The newest release on a channel, shaped for the Updater;
    # raises on any failure and lets the caller word it. Stable
    # asks GitHub for its "latest" — by GitHub's own rule the
    # newest non-prerelease, the main branch's line. Edge reads
    # the release list and takes the newest published entry,
    # pre-releases included — the dev branch's line, kept
    # separate from main, which is what an Edge build is.
    feed_url = os.environ.get("NAVI_UPDATE_FEED_URL") or ""
    if feed_url:
        rel = github_json(feed_url)
        if not isinstance(rel, dict):
            raise ValueError("GitHub's answer was not a release record.")
        return _shape_release(rel)
    if channel == "edge":
        items = github_json(GITHUB_API_BASE + "/releases?per_page=10")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and not item.get("draft"):
                    return _shape_release(item)
        raise ValueError("GitHub's release list carried no published release.")
    rel = github_json(GITHUB_API_BASE + "/releases/latest")
    if not isinstance(rel, dict):
        raise ValueError("GitHub's answer was not a release record.")
    return _shape_release(rel)


def current_release(cfg=None):
    # The release page for the version this install is running —
    # the Updater's "About this release" dropdown reads it: name,
    # tag, date, link, and the full notes, from the release page
    # itself. Best-effort: any failure answers None and the panel
    # says the page could not be fetched; it never invents one.
    number = app_version(cfg)
    status = app_version_status(cfg)
    tags = [_version_label(number, status), "v" + str(number)]
    seen = []
    for t in tags:
        if t and t not in seen:
            seen.append(t)
    for tag in seen:
        try:
            rel = github_json(GITHUB_API_BASE + "/releases/tags/" + tag)
        except Exception:
            continue
        if isinstance(rel, dict) and rel.get("tag_name"):
            return _shape_release(rel)
    return None


def changelog_section_for(tag):
    # The CHANGELOG fallback for the Updater's release notes
    # (build .70, issue #47): when a release is published with an
    # empty body, the panel still deserves the notes, so the
    # bridge reads the project's CHANGELOG.md from the repo and
    # cuts out the section for the release's version — the
    # "## 0.1.6 (alpha)" heading down to the next "## " heading.
    # Any failure (offline, no such section) returns "" and the
    # panel simply shows no notes; it never invents any.
    number, _status = _tag_parts(tag)
    if not number:
        return ""
    try:
        text = github_text(
            "https://raw.githubusercontent.com/AlexKollar/Apex/main/CHANGELOG.md",
            "text/plain")
    except Exception:
        return ""
    lines = str(text).splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            head = line[3:].strip()
            head_number = head.split(" ")[0].split("(")[0].strip()
            if head_number == number:
                start = i
                break
    if start is None:
        return ""
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


# -- Background update re-check (build .86) -------------------------
# While the bridge runs, a daemon thread re-checks for updates on
# its own: shortly after startup, then every 3 hours, on the
# install's configured channel. The verdict is cached here and
# /api/status carries it as its "update" object, so the dashboard
# learns about an update without the operator ever opening the
# Updater. Silent by design — no UI of its own, no nag; the
# status line's single "Up to date" / "Update available" voice is
# still the only voice.
UPDATE_BG_STATE = {"payload": None}
UPDATE_BG_LOCK = threading.Lock()


def update_bg_payload():
    with UPDATE_BG_LOCK:
        return UPDATE_BG_STATE["payload"]


def _update_bg_loop():
    time.sleep(20)
    while True:
        try:
            cfg = load_config()
            res = update_check_payload(cfg)
            payload = {
                "updateAvailable": bool(res.get("updateAvailable")),
                "latest": res.get("latest") or "",
                "channel": res.get("channel") or updater_channel(cfg),
                "checkedAt": res.get("checkedAt") or "",
            }
            with UPDATE_BG_LOCK:
                UPDATE_BG_STATE["payload"] = payload
        except Exception:
            pass
        time.sleep(3 * 3600)


def update_check_payload(cfg=None, channel=None):
    current = app_version(cfg)
    current_status = app_version_status(cfg)
    # Channel resolution (Build 2): a persisted explicit choice is
    # authoritative — the check follows the channel the operator
    # picked, and the payload says so (channelExplicit). With no
    # explicit choice, an Edge build checks Edge even when the
    # caller asks for "stable": the only caller that asks is a
    # dashboard whose baked starting channel predates the choice,
    # and that inherited word is not a choice (see
    # updater_channel). On a Stable build with no explicit choice,
    # the caller's channel is honored, else the effective default.
    if updater_channel_explicit(cfg):
        channel = updater_channel(cfg)
    elif current_status == "edge":
        channel = "edge"
    elif channel not in ("stable", "edge"):
        channel = updater_channel(cfg)
    base = {
        "current": current,
        "currentStatus": current_status,
        "channel": channel,
        "channelExplicit": updater_channel_explicit(cfg),
        "checkedAt": _now_iso(),
    }
    try:
        rel = latest_release(channel)
    except Exception as e:
        return dict(base, ok=False, updateAvailable=False, latest="",
                    error=_update_error_text(e))
    newer = bool(rel["tag"]) and _release_is_newer(
        rel["tag"], current, current_status, rel.get("buildSeq"))
    # The release's notes travel with the check result (build .70,
    # issue #47): the Updater panel reads them before offering the
    # install, and Apply never fetches them again. Source of truth
    # is the release body; an empty body falls back to the matching
    # CHANGELOG section, and notesSource says which one answered,
    # so the panel can label the fallback honestly.
    notes = rel["notes"]
    notes_source = "release" if notes.strip() else ""
    if newer and not notes_source:
        fallback = changelog_section_for(rel["tag"])
        if fallback:
            notes = fallback
            notes_source = "changelog"
    # The running version's own release page rides the same check
    # (build .83): the panel's "About this release" dropdown shows
    # everything that page offers without a second round trip.
    cur_rel = current_release(cfg)
    if cur_rel is not None and not cur_rel["notes"].strip():
        fb = changelog_section_for(cur_rel["tag"])
        if fb:
            cur_rel = dict(cur_rel, notes=fb, notesSource="changelog")
    return dict(
        base, ok=True, updateAvailable=newer,
        latest=rel["tag"], releaseName=rel["name"],
        releaseUrl=rel["url"], publishedAt=rel["publishedAt"],
        prerelease=rel["prerelease"],
        buildSeq=rel.get("buildSeq"), currentBuildSeq=SHIPPED_BUILD_SEQ,
        notes=notes, notesSource=notes_source, asset=rel["asset"],
        currentRelease=cur_rel,
    )


def _version_label(number, status):
    # The footer's version-label form: "v" + number + the status
    # letter (e for edge, b for beta, none for a full release) —
    # the form the Updater's confirmation line uses for both
    # sides of "Updated v0.1.6a → v0.1.7" (the from-side's "a" is
    # a legacy tag from before the sync; it is read, never made).
    return "v" + str(number) + (
        "e" if status in ("edge", "alpha") else
        "b" if status == "beta" else "")


def _tag_parts(tag):
    # A release tag in the label's shape — "v0.1.8e", "v0.1.7",
    # "v0.1.8-edge" — split into (number, status). The retired
    # alpha forms ("v0.1.6a", "-alpha") parse as edge: they were
    # pre-releases then and are pre-releases now.
    text = str(tag or "").strip()
    if text.lower().startswith("v"):
        text = text[1:]
    status = "stable"
    low = text.lower()
    for word in ("edge", "beta", "alpha"):
        if low.endswith("-" + word) or low.endswith(" " + word):
            status = "edge" if word == "alpha" else word
            text = text[: -(len(word) + 1)]
            low = text.lower()
            break
    if (status == "stable" and len(text) > 1
            and text[-1].lower() in ("e", "a", "b") and text[-2].isdigit()):
        status = "beta" if text[-1].lower() == "b" else "edge"
        text = text[:-1]
    return text, status


def _write_update_result(rec):
    try:
        # Build 5: every write carries a freshness stamp, so a
        # reader can always tell a live apply from an orphaned
        # one (see the apply watchdog below).
        rec["updatedAt"] = _now_iso()
        rec["updatedEpoch"] = time.time()
        os.makedirs(os.path.dirname(UPDATE_RESULT_PATH), exist_ok=True)
        tmp = UPDATE_RESULT_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(rec, f)
        os.replace(tmp, UPDATE_RESULT_PATH)
    except Exception:
        pass


def _apply_watchdog(rec):
    # The apply watchdog (Build 5): the backstop for the one
    # death the detached helper cannot record itself — killed
    # outright (SIGKILL, the kernel OOM killer, power loss)
    # before it could write again, like the silent death the
    # Build 4 round-trip gate found, where the record froze at
    # working/installing for a quarter of an hour and nothing
    # ever closed it. When a record still claims "working" but
    # its helper process is gone and its last write is stale,
    # the record is closed HERE, by whichever bridge serves it
    # next: state failed, the step it died on kept, and the
    # error quoting the helper step log's last line (the last
    # step the helper provably completed). A helper that is
    # still alive is never touched: the install step can
    # legitimately run silent for many minutes while the
    # installer rebuilds, and only a dead pid plus a stale
    # record convicts. Records with no helper pid (written
    # before pids were recorded) are judged on staleness alone,
    # against a threshold longer than any silent step.
    try:
        if rec.get("state") != "working":
            return rec
        try:
            stale = time.time() - os.path.getmtime(UPDATE_RESULT_PATH)
        except Exception:
            return rec
        pid = rec.get("helperPid")
        alive = None
        if pid:
            try:
                alive = pid_alive(int(pid))
            except Exception:
                alive = None
        if alive:
            return rec
        if alive is False and stale <= 30:
            return rec
        if alive is None and stale <= 360:
            return rec
        step = rec.get("step") or "installing"
        last = ""
        trace_path = rec.get("traceLog") or ""
        if trace_path:
            try:
                with open(trace_path, "rb") as f:
                    lines = f.read().decode(
                        "utf-8", "replace").strip().splitlines()
                if lines:
                    last = lines[-1].strip()
            except Exception:
                last = ""
        rec["state"] = "failed"
        rec["failedAt"] = _now_iso()
        rec["watchdog"] = True
        rec["error"] = (
            "The apply helper stopped at the " + step + " step "
            "and never finished this record — the apply watchdog "
            "closed it, because the helper process is gone and "
            "the record went stale. Nothing is confirmed updated."
            + (" Its step log ends with: " + last if last else "")
            + " The staged package is still in place — the "
            "manual fallback below finishes the job by hand.")
        _write_update_result(rec)
        return rec
    except Exception:
        return rec


def update_result_payload():
    # The apply's live record (config/update-result.json): the
    # step it is on while it runs, and afterwards either the
    # confirmed outcome or the failure + fallback. No record yet
    # reads as state "none". A record orphaned by a helper that
    # died outright is closed by the apply watchdog on its way
    # out (Build 5) — never left claiming "working" forever.
    try:
        with open(UPDATE_RESULT_PATH) as f:
            rec = json.load(f)
        if isinstance(rec, dict):
            return dict(_apply_watchdog(rec), ok=True)
    except Exception:
        pass
    return {"ok": True, "state": "none"}


def _unwrap_package(data):
    # The download validator's front door (build .56): returns
    # (payload, note) — payload is the zip bytes to verify, note
    # says how they arrived ("" for a plain zip, "gzip" when a
    # gzip wrapper was unwrapped). When neither the raw payload
    # nor its unwrapped form can be a zip, payload is None and
    # note names the shape that failed ("gzip-broken",
    # "gzip-not-zip"); a plain non-zip payload comes back as-is
    # and fails the zip check with the classic wording, exactly
    # as before.
    if data[:2] == bytes([0x1F, 0x8B]):
        try:
            inner = gzip.decompress(data)
        except Exception:
            return None, "gzip-broken"
        if inner[:2] == b"PK":
            return inner, "gzip"
        return None, "gzip-not-zip"
    return data, ""


# The detached apply helper, written by the bridge into
# updates/<tag>/apply-helper.py at apply time and spawned in its
# own session so it outlives the bridge: it runs the staged
# installer (never --fresh — persistence is the installer's own
# stash-and-restore), relaunches the app through start.sh, and
# finishes the update-result record the panel reads. It is a
# standalone stdlib script: everything it needs arrives in the
# job file beside it. Since Build 5 it also keeps the step log
# (apply-trace.log) described in its own header: the Build 4
# round-trip gate caught the old helper dying traceless
# between the installer's "Done." and the relaunch — no log,
# no record update, no relaunch — and the repair is structural
# (trace from the first instruction, a top-level guard, signal
# handlers, a heartbeat, and the bridge-side apply watchdog in
# update_result_payload above), not a patch on one suspect
# line.
APPLY_HELPER_PY = '''#!/usr/bin/env python3
# Apex updater apply helper — written by bridge.py into
# updates/<tag>/ and run detached (its own session), so it
# outlives the bridge it replaces. It runs the staged installer
# (never --fresh), relaunches the app through start.sh, and
# records the outcome in config/update-result.json — the record
# the Updater panel reads its confirmation (or its failure and
# fallback) from. Stdlib only, like the bridge.
#
# Build 5 — the helper can no longer die traceless. The Build 4
# round-trip gate caught it dying silently: the installer ran
# through to "Done.", then nothing — apply.log 0 bytes, no
# relaunch log, the record frozen at working/installing, no
# bridge relaunched. The old helper's only diary was the record
# itself, it wrote the record only at step boundaries, it had
# no top-level guard, no signal handlers, and it printed
# nothing — so any death between two writes (a signal above
# all: an uncaught Python exception would at least have left a
# traceback in apply.log, and apply.log was empty) left no
# evidence at all. Now, from its first instruction, the helper
# keeps a step log — apply-trace.log beside the job file, its
# path carried on the apply record — and writes every step
# boundary, a 30-second heartbeat while it works, every signal
# it is handed, and every exception into that log and onto the
# record (state/step/updatedAt) as it happens. A top-level
# guard turns any Python-level failure into a failed record
# naming the step and the reason before exiting, and mirrors
# the traceback to stderr so apply.log is never 0 bytes on a
# death words could have described. Signal handlers do the
# same for SIGTERM, SIGINT and SIGHUP. The one death no
# in-process guard can survive — SIGKILL, the kernel OOM
# killer, power loss — still leaves the step log ending at the
# last completed step, and the bridge's apply watchdog closes
# a record whose helper is gone as failed at that step,
# quoting the log's last line, instead of leaving it frozen
# at working/installing forever.
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request

STATE = {"step": "starting", "job": None, "env": None,
         "trace_path": None, "result_path": None,
         "stop_beat": False}


def _stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def trace(event, detail=""):
    # The step log: append-only, flushed and fsync'd per line,
    # and never allowed to raise — a helper that dies because
    # its own diary failed would be the old bug in a new coat.
    path = STATE.get("trace_path")
    if not path:
        return
    try:
        line = _stamp() + " [" + str(STATE.get("step")) + "] " + event
        if detail:
            line += " — " + str(detail)
        with open(path, "a") as f:
            f.write(line + "\\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def write_result(patch):
    # The apply record: read-modify-write like always, now
    # stamped with the current step and a freshness time on
    # EVERY write, so the panel — and the bridge's apply
    # watchdog — can always tell a live helper from a dead
    # one. Never raises: a failed record write is traced and
    # retried once, and the step log still carries what the
    # record could not.
    job = STATE.get("job") or {}
    result_path = STATE.get("result_path") or job.get("resultPath")
    if not result_path:
        return
    patch = dict(patch)
    if "step" in patch:
        STATE["step"] = patch["step"]
    patch.setdefault("step", STATE.get("step"))
    patch["updatedAt"] = _stamp()
    patch["updatedEpoch"] = time.time()
    patch["helperStep"] = STATE.get("step")
    if job.get("traceLog"):
        patch["traceLog"] = job["traceLog"]
    for attempt in (1, 2):
        try:
            rec = {}
            try:
                with open(result_path) as f:
                    rec = json.load(f)
                if not isinstance(rec, dict):
                    rec = {}
            except Exception:
                rec = {}
            rec.update(patch)
            tmp = result_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(rec, f)
            os.replace(tmp, result_path)
            trace("record",
                  "state=" + str(rec.get("state"))
                  + " step=" + str(rec.get("step")))
            return
        except Exception as e:
            trace("record-write-failed",
                  "attempt " + str(attempt) + ": " + str(e))


def fail(step, error):
    STATE["step"] = step
    job = STATE.get("job") or {}
    write_result({
        "state": "failed", "step": step, "error": error,
        "stagedDir": job.get("pkgDir", ""),
        "command": job.get("command", ""),
        "failedAt": _stamp(),
    })


def _heartbeat():
    # While the helper lives it beats every 30 seconds into the
    # step log, naming the step it is on. A log whose beats stop
    # mid-step is a killed helper; a log still beating at one
    # step is a blocked one — the field can finally tell those
    # two deaths apart, which the frozen Build 4 record could
    # not.
    while not STATE.get("stop_beat"):
        time.sleep(30)
        if STATE.get("stop_beat"):
            break
        trace("heartbeat", "still working")


def _on_signal(signum, frame):
    # SIGTERM / SIGINT / SIGHUP get words before the exit: the
    # step log and the record both name the signal and the step
    # it interrupted, so a helper stopped from outside is a
    # recorded failure, never a silent freeze. (SIGKILL cannot
    # be handled by any process — the step log's last line and
    # the bridge's apply watchdog cover that death.)
    name = "signal " + str(signum)
    try:
        name = signal.Signals(signum).name
    except Exception:
        pass
    trace("signal", name + " received — recording the failure and exiting")
    job = STATE.get("job") or {}
    try:
        write_result({
            "state": "failed", "step": STATE.get("step"),
            "error": (
                "The apply helper was stopped by " + name
                + " at the " + str(STATE.get("step")) + " step, "
                "so the update is not confirmed. Its step log "
                "(apply-trace.log, beside the staged package) "
                "shows the last step it completed. The staged "
                "package is still in place — the manual fallback "
                "below finishes the job by hand."),
            "stagedDir": job.get("pkgDir", ""),
            "command": job.get("command", ""),
            "failedAt": _stamp(),
        })
    except Exception:
        pass
    os._exit(128 + signum)


def version_tuple(raw):
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


def tuples_equal(a, b):
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) == b + (0,) * (width - len(b))


def read_installed_version(root):
    # The VERSION file at the install root, parsed the way the
    # bridge parses it: (number, status).
    try:
        with open(os.path.join(root, "VERSION")) as f:
            text = f.read().strip()
    except Exception:
        return "", "stable"
    if not text:
        return "", "stable"
    raw = text.splitlines()[0].strip()
    status = "stable"
    low = raw.lower()
    for word in ("edge", "beta", "alpha"):
        if low.endswith(" " + word) or low.endswith("-" + word):
            status = "edge" if word == "alpha" else word
            raw = raw[: -(len(word) + 1)]
            break
    parts = raw.split()
    token = parts[0] if parts else ""
    for word in ("edge", "alpha", "beta", "stable"):
        if token.lower().endswith("-" + word):
            token = token[: -(len(word) + 1)]
            break
    return token, status


def read_installed_build_seq(root):
    # The Edge build sequence baked into the bridge.py at the
    # install root (Build 4): the on-disk half of the identity a
    # same-version refresh has to prove, beside the VERSION
    # file's number — which a refresh deliberately does not
    # change. None when the file or the sequence cannot be read
    # (a bridge from before build sequences existed).
    try:
        with open(os.path.join(root, "bridge.py"), "rb") as f:
            m = re.search(
                rb"SHIPPED_BUILD_SEQ\\s*=\\s*([0-9]+)", f.read())
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _pid_gone(pid):
    # Gone = no such process, or a zombie: a zombie holds no
    # sockets (the kernel closed them at death) and its parent
    # reaps it in its own time.
    if not pid:
        return True
    if not _pid_alive(pid):
        return True
    try:
        with open("/proc/" + str(pid) + "/stat", "rb") as f:
            parts = f.read().rsplit(b")", 1)
        state = parts[1].split()[0].decode("utf-8", "replace") if len(parts) > 1 else ""
        return state == "Z"
    except Exception:
        return False


def _pid_cmdline(pid):
    try:
        with open("/proc/" + str(pid) + "/cmdline", "rb") as f:
            raw = f.read()
        return " ".join(part.decode("utf-8", "replace") for part in raw.split(bytes([0]))).strip()
    except Exception:
        return ""


def _pid_cwd(pid):
    try:
        return os.path.realpath(os.readlink("/proc/" + str(pid) + "/cwd"))
    except Exception:
        return ""


def _port_holder_pid(port):
    # The PID holding the LISTEN socket on the port, resolved from
    # /proc alone — names a holder that answers nothing, where a
    # status probe can only shrug.
    inodes = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                rows = f.read().splitlines()[1:]
        except Exception:
            continue
        for row in rows:
            parts = row.split()
            if len(parts) > 9 and parts[3] == "0A":
                try:
                    if int(parts[1].rsplit(":", 1)[1], 16) == port:
                        inodes.add(parts[9])
                except Exception:
                    pass
    if not inodes:
        return None
    targets = set("socket:[" + ino + "]" for ino in inodes)
    try:
        names = os.listdir("/proc")
    except Exception:
        return None
    for name in names:
        if not name.isdigit():
            continue
        try:
            fds = os.listdir("/proc/" + name + "/fd")
        except Exception:
            continue
        for fd in fds:
            try:
                if os.readlink("/proc/" + name + "/fd/" + fd) in targets:
                    return int(name)
            except Exception:
                pass
    return None


def _port_answers_expected(port, tgt_seq):
    # True when the bridge answering on the port already reports
    # the target identity — the case where a relaunch spawn
    # failure must NOT fail the apply: the installer's own
    # relaunch (build .91) already brought the new bridge up.
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(port) + "/api/status",
            headers={"User-Agent": "navi-update-helper"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            seen = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return False
    if not isinstance(seen, dict) or seen.get("app") != "Navi: Apex":
        return False
    return tgt_seq is None or seen.get("buildSeq") == tgt_seq


def _holder_remedy(port):
    # The failure-text remedy for a held port (build .91): name
    # the holder and its exact kill command when the socket can
    # resolve it — never "launch the app again" against a wedged
    # port, the advice that stranded the field update this build
    # answers.
    holder = _port_holder_pid(port)
    if holder:
        cmd = _pid_cmdline(holder)
        return ("The port is held by process " + str(holder)
                + (" (" + cmd + ")" if cmd else "")
                + ": end it with kill -9 " + str(holder)
                + ", then run the update again — launching the app "
                "again cannot work while that process holds the port.")
    return ("If a process is holding the port, find it with lsof -i :"
            + str(port) + " and end it, then run the update again; "
            "otherwise launch the app again from its menu entry.")


def clear_wedged_bridge(root, port, tgt_seq):
    # Build .91 (issue #91): before relaunching, prove the OLD
    # bridge is actually gone — not merely that its pid file is.
    # A bridge can still hold the port while answering nothing
    # (frozen, stopped, stuck mid-work), and every relaunch
    # against it is a no-op: the new bridge cannot bind, and the
    # confirmation that follows can only report failure with a
    # remedy that cannot work. If the target build already
    # answers, there is nothing to clear; if the port is free,
    # likewise. A holder is signalled ONLY when it is provably
    # this install's bridge — bridge.py in its command line AND
    # its working directory the install root; anything else is
    # reported, never touched. Escalation mirrors the installer:
    # SIGTERM, wait for death AND a free port, SIGKILL, wait
    # again. Returns (ok, holder_pid, holder_desc).
    if _port_answers_expected(port, tgt_seq):
        return (True, None, "")
    holder = _port_holder_pid(port)
    if holder is None:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=2)
            sock.close()
            return (False, None,
                    "something is listening on the port but its process could not be identified")
        except Exception:
            return (True, None, "")
    cmd = _pid_cmdline(holder)
    desc = "process " + str(holder) + ((" (" + cmd + ")") if cmd else "")
    owned = ("bridge.py" in cmd) and (_pid_cwd(holder) == os.path.realpath(root))
    if not owned:
        return (False, holder, desc + " — not this install's bridge, so it was not touched")
    trace("wedge-clear",
          "wedged bridge " + desc + " — escalating: SIGTERM, then SIGKILL if it holds")
    try:
        os.kill(holder, signal.SIGTERM)
    except Exception:
        pass
    deadline = time.time() + 15
    while time.time() < deadline:
        if _pid_gone(holder) and _port_holder_pid(port) is None:
            trace("wedge-clear", "holder gone after SIGTERM; the port is free")
            return (True, holder, desc)
        time.sleep(0.5)
    try:
        os.kill(holder, signal.SIGKILL)
    except Exception:
        pass
    deadline = time.time() + 10
    while time.time() < deadline:
        if _pid_gone(holder) and _port_holder_pid(port) is None:
            trace("wedge-clear", "holder gone after SIGKILL; the port is free")
            return (True, holder, desc)
        time.sleep(0.5)
    return (False, holder, desc)


def version_label(number, status):
    return "v" + number + (
        "e" if status in ("edge", "alpha") else
        "b" if status == "beta" else "")


def main():
    job_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if job_path:
        STATE["trace_path"] = os.path.join(
            os.path.dirname(os.path.abspath(job_path)),
            "apply-trace.log")
    trace("helper-start",
          "pid " + str(os.getpid()) + ", job " + (job_path or "(none)"))
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _on_signal)
        except Exception as e:
            trace("signal-handler-skipped", str(e))
    beat = threading.Thread(target=_heartbeat, daemon=True)
    beat.start()
    with open(job_path) as f:
        job = json.load(f)
    STATE["job"] = job
    if job.get("traceLog"):
        STATE["trace_path"] = job["traceLog"]
    root = job["root"]
    STATE["result_path"] = job["resultPath"]
    pkg_dir = job["pkgDir"]
    trace("job-loaded",
          "target " + str(job.get("targetLabel"))
          + ", target build " + str(job.get("targetBuildSeq")))

    env = dict(os.environ)
    env["NAVI_HOME"] = root
    STATE["env"] = env

    def relaunch():
        try:
            log = open(job["relaunchLog"], "ab")
            subprocess.Popen(
                ["bash", os.path.join(root, "start.sh")],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, close_fds=True)
            trace("relaunch", "start.sh spawned")
            return ""
        except Exception as e:
            trace("relaunch-failed", str(e))
            return str(e)

    # Give the bridge a moment to answer the apply request and
    # the panel a moment to paint the installing step before the
    # installer stops the bridge.
    time.sleep(2)
    STATE["step"] = "installing"
    write_result({"state": "working", "step": "installing"})
    startup = "boot" if job.get("startup") == "on-boot" else "launch"
    # The install's known answers ride as flags (build .84, issue
    # #75): this run is detached and terminal-less by design, so
    # the installer is never left to ask a question nobody can
    # answer — startup from the config (above), voice from whether
    # her venv is on disk, both recorded on the job by the bridge
    # when it staged the update.
    voice = "yes" if job.get("voice") == "yes" else "no"
    code = None
    why = ""
    trace("installer-start",
          "bash install.sh --startup " + startup + " --voice " + voice)
    try:
        with open(job["installLog"], "wb") as log:
            proc = subprocess.run(
                ["bash", os.path.join(pkg_dir, "install.sh"),
                 "--startup", startup, "--voice", voice,
                 "--dir", root],
                cwd=pkg_dir, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=3000)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        why = "the installer did not finish within 50 minutes"
    except Exception as e:
        why = str(e)
    trace("installer-exit",
          "code " + str(code) + ((", " + why) if why else ""))

    if code != 0:
        reason = why or ("it exited with code " + str(code))
        fail("install",
             "Installing the update failed — " + reason + ". The "
             "installer's own output is in updates/" + job["tagDir"]
             + "/apply-install.log. Nothing is confirmed updated: "
             "the app is being relaunched as it lies, and the "
             "staged package is still in place — the manual "
             "fallback below finishes the job by hand.")
        relaunch()
        STATE["stop_beat"] = True
        return

    # The installer's DHD prerequisite step is a named ladder
    # step of its own: its summary line is read back from the
    # install log the helper just captured, so the panel shows
    # the step because the installer really ran it — never as a
    # file-copy shortcut or a relabelled install phase.
    dhd_prereq_detail = ""
    try:
        with open(job["installLog"], "rb") as log:
            install_text = log.read().decode("utf-8", "replace")
        for line in install_text.splitlines():
            if line.startswith("DHD-PREREQS:"):
                dhd_prereq_detail = line.split(":", 1)[1].strip()
                break
    except Exception:
        dhd_prereq_detail = ""
    trace("dhd-prereqs",
          dhd_prereq_detail or "no DHD-PREREQS line in the install log")
    STATE["step"] = "dhd-prereqs"
    write_result({
        "state": "working", "step": "dhd-prereqs",
        "dhdPrereqs": dhd_prereq_detail or "This installer did not report a DHD prerequisite step.",
    })
    time.sleep(1)
    STATE["step"] = "restarting"
    write_result({"state": "working", "step": "restarting"})
    # Build .91 (issue #91): prove the old bridge is gone BEFORE
    # relaunching. A wedged holder makes every relaunch a no-op —
    # the new bridge cannot bind — and the old failure text's
    # remedy ("launch the app again") cannot work while the port
    # is held. Escalate here exactly as the installer does; if
    # the port still cannot be cleared, fail naming the holder
    # and the exact command that ends it.
    wedge_ok, wedge_pid, wedge_desc = clear_wedged_bridge(
        root, job["port"], job.get("targetBuildSeq"))
    if not wedge_ok:
        if wedge_pid:
            wedge_remedy = (
                "End it with: kill -9 " + str(wedge_pid)
                + " — then run the update again, or the manual "
                "fallback below. Launching the app again cannot "
                "work while that process holds the port.")
        else:
            wedge_remedy = (
                "Find what holds it with: lsof -i :" + str(job["port"])
                + " — end that process, then run the update again, "
                "or the manual fallback below. Launching the app "
                "again cannot work while the port is held.")
        fail("restart",
             "The update installed, but the old bridge could not "
             "be cleared from http://localhost:" + str(job["port"])
             + ": " + wedge_desc + ". The new bridge cannot start "
             "while the port is held, so the update is not "
             "confirmed. " + wedge_remedy
             + " The staged package is still in place.")
        STATE["stop_beat"] = True
        return
    relaunch_err = relaunch()
    if relaunch_err:
        if _port_answers_expected(job["port"], job.get("targetBuildSeq")):
            # The spawn failed but the target build is already
            # answering — the installer's own relaunch (build
            # .91) brought her up. Not a failure: fall through to
            # the confirmation loop, which will see her itself.
            trace("relaunch-skipped",
                  "spawn failed (" + relaunch_err + ") but the target build already answers")
            relaunch_err = ""
        else:
            fail("restart",
                 "The update installed, but relaunching Apex through "
                 "start.sh could not even be started (" + relaunch_err
                 + "), so the update is not confirmed. Expected "
                 + job["targetLabel"]
                 + (" Build " + str(job["targetBuildSeq"])
                    if job.get("targetBuildSeq") is not None else "")
                 + " answering on http://localhost:" + str(job["port"])
                 + "; found: no relaunch was started. The staged "
                 "package is still in place — the manual fallback "
                 "below finishes the job by hand, or launch the app "
                 "again from its menu entry.")
            STATE["stop_beat"] = True
            return
    target = tuple(job["targetTuple"])
    # Build 4: when the job names a target Build number, the
    # confirmation must observe that build answering — the
    # version number is identical on both sides of a refresh,
    # so a version-only match once certified the previous
    # build's reinstall as the new build's arrival.
    tgt_seq = job.get("targetBuildSeq")
    answered = None
    last_seen = ""
    deadline = time.time() + 300
    while time.time() < deadline:
        seen = None
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:" + str(job["port"]) + "/api/status",
                headers={"User-Agent": "navi-update-helper"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                seen = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception:
            seen = None
        if seen:
            last_seen = (
                "app=" + str(seen.get("app"))
                + " version=" + str(seen.get("version"))
                + " buildSeq=" + str(seen.get("buildSeq")))
        if seen and seen.get("app") == "Navi: Apex":
            if answered is None:
                trace("bridge-answered", last_seen)
            answered = seen
            if (seen.get("version")
                    and tuples_equal(
                        version_tuple(seen["version"]), target)
                    and (tgt_seq is None
                         or seen.get("buildSeq") == tgt_seq)):
                break
        time.sleep(2)
    after_number, after_status = read_installed_version(root)
    after_label = (
        version_label(after_number, after_status) if after_number else "")
    disk_seq = read_installed_build_seq(root)
    trace("confirm",
          "live: " + (last_seen or "no answer")
          + "; on disk: version=" + (after_number or "(unreadable)")
          + " buildSeq=" + str(disk_seq)
          + "; expected: " + job["targetLabel"]
          + " buildSeq=" + str(tgt_seq))
    live_ok = bool(
        answered and answered.get("version")
        and tuples_equal(version_tuple(answered["version"]), target)
        and (tgt_seq is None or answered.get("buildSeq") == tgt_seq))
    file_ok = bool(
        after_number
        and tuples_equal(version_tuple(after_number), target)
        and (tgt_seq is None or disk_seq is None
             or disk_seq == tgt_seq))
    if live_ok and file_ok:
        STATE["step"] = "done"
        write_result({
            "state": "done", "step": "done",
            "afterVersion": after_number,
            "afterStatus": after_status,
            # The worker's composed to-side label when it sent
            # one (Build 3: a refresh's "Build <n>"); the label
            # read from the VERSION file otherwise — identical
            # for graduations and new versions.
            "afterLabel": job.get("afterLabel") or after_label,
            "updatedAt": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        trace("done",
              "confirmed " + str(job.get("afterLabel") or after_label))
    elif answered is None:
        fail("restart",
             "The update installed, but Apex did not answer on "
             "http://localhost:" + str(job["port"]) + " after "
             "restarting, so the update is not confirmed. Expected "
             + job["targetLabel"]
             + (" Build " + str(tgt_seq) if tgt_seq is not None else "")
             + " answering there; found: "
             + (("an answer that was not the expected bridge ("
                 + last_seen + ")")
                if last_seen else
                "no answer at all in five minutes")
             + ". "
             + _holder_remedy(job["port"])
             + " The staged package is still in place — the manual "
             "fallback below re-runs its installer by hand.")
    elif (tgt_seq is not None and disk_seq is not None
            and disk_seq != tgt_seq):
        fail("restart",
             "Apex came back after the update, but the bridge "
             "installed on disk is Build " + str(disk_seq)
             + " instead of the expected Build " + str(tgt_seq)
             + " — the update is not confirmed. The staged "
             "package is still in place — the manual fallback "
             "below finishes the job by hand.")
    elif (tgt_seq is not None and answered is not None
            and answered.get("buildSeq") is not None
            and answered.get("buildSeq") != tgt_seq):
        fail("restart",
             "Apex came back after the update, but the bridge "
             "answering reports Build "
             + str(answered.get("buildSeq"))
             + " instead of the expected Build " + str(tgt_seq)
             + " — the update is not confirmed. "
             + _holder_remedy(job["port"])
             + " The staged package is still in place — the manual "
             "fallback below finishes the job by hand.")
    else:
        fail("restart",
             "Apex came back after the update, but its VERSION "
             "file reads " + (after_label or "nothing readable")
             + " instead of the expected " + job["targetLabel"]
             + " — the update is not confirmed. The staged "
             "package is still in place — the manual fallback "
             "below finishes the job by hand.")
    STATE["stop_beat"] = True


def _guarded_main():
    # The top-level guard: any Python-level failure anywhere in
    # the apply — the job load, a record write, the relaunch,
    # the confirmation — lands in the step log with its
    # traceback, in the record as a failed state naming the
    # step it died on and the reason in words, and on stderr
    # (which the bridge points at apply.log, so that file is
    # never again 0 bytes on a death words could describe).
    try:
        main()
    except BaseException as e:
        tb = traceback.format_exc()
        trace("fatal", tb.replace("\\n", " | ")[-1500:])
        try:
            print(tb, file=sys.stderr)
            sys.stderr.flush()
        except Exception:
            pass
        job = STATE.get("job") or {}
        try:
            write_result({
                "state": "failed", "step": STATE.get("step"),
                "error": (
                    "The apply helper failed at the "
                    + str(STATE.get("step")) + " step: "
                    + type(e).__name__ + ": " + str(e)
                    + " — the update is not confirmed. Its step "
                    "log (apply-trace.log, beside the staged "
                    "package) carries the full trace. The staged "
                    "package is still in place — the manual "
                    "fallback below finishes the job by hand."),
                "stagedDir": job.get("pkgDir", ""),
                "command": job.get("command", ""),
                "failedAt": _stamp(),
            })
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    _guarded_main()
'''


_update_apply_lock = threading.Lock()
_update_apply_state = {"running": False}


def _run_update_apply(cfg):
    # The apply worker (build .56): download -> verify -> stage on
    # this thread, writing each step into the update record, then
    # hand the install itself to the detached helper and finish.
    # Every failure lands in the record with its step named; a
    # failure before staging completes carries no fallback (there
    # is no complete staged package to fall back to), and nothing
    # is extracted before the package verifies.
    record = {
        "state": "working", "step": "downloading",
        "startedAt": _now_iso(),
    }
    staged = {"dir": "", "command": ""}

    def fail(step, error):
        record["state"] = "failed"
        record["step"] = step
        record["error"] = error
        record["failedAt"] = _now_iso()
        if staged["dir"]:
            record["stagedDir"] = staged["dir"]
            record["command"] = staged["command"]
        _write_update_result(record)

    try:
        current = app_version(cfg)
        current_status = app_version_status(cfg)
        record["beforeVersion"] = current
        record["beforeStatus"] = current_status
        record["beforeLabel"] = _version_label(current, current_status)
        try:
            rel = latest_release(updater_channel(cfg))
        except Exception as e:
            fail("downloading",
                 "Downloading the update failed — the release check "
                 "did not complete: " + _update_error_text(e))
            return
        tag = rel["tag"]
        t_num, t_status = _tag_parts(tag)
        record["tag"] = tag
        record["targetLabel"] = (
            _version_label(t_num, t_status) if t_num else tag)
        # Build 3: a same-version refresh — same numbers, same
        # status, a higher Build number — names the builds in its
        # labels, because the plain version labels read as no
        # change at all ("Updated v0.1.8e → v0.1.8e"). The pair
        # reads "v0.1.8e Build 2 → Build 3": the from-side keeps
        # its version (it says what was running), the to-side is
        # just the build it lands on. Graduation and new-version
        # updates keep the plain version labels, untouched.
        _tgt_seq = rel.get("buildSeq")
        if t_num and current_status == "edge" and _tgt_seq is not None                 and _tgt_seq > SHIPPED_BUILD_SEQ:
            _a, _b = _version_tuple(t_num), _version_tuple(current)
            _w = max(len(_a), len(_b))
            _same_numbers = (_a + (0,) * (_w - len(_a))) == (
                _b + (0,) * (_w - len(_b)))
            if _same_numbers and _status_rank(t_status) == _status_rank(
                    current_status):
                record["beforeLabel"] = (
                    record["beforeLabel"] + " Build "
                    + str(SHIPPED_BUILD_SEQ))
                record["targetLabel"] = "Build " + str(_tgt_seq)
        if not tag or not _release_is_newer(tag, current, current_status, rel.get("buildSeq")):
            fail("downloading",
                 "The latest release (" + (tag or "none") + ") is not "
                 "newer than the running v" + current
                 + " — nothing was downloaded.")
            return
        asset = rel["asset"]
        if not asset or not asset["url"]:
            fail("downloading",
                 "The latest release carries no package .zip asset, "
                 "so there is nothing to download.")
            return
        record["assetName"] = asset["name"]
        tag_dir = re.sub(r"[^0-9A-Za-z._-]+", "-", tag) or "release"
        stage_root = os.path.join(UPDATES_DIR, tag_dir)
        pkg_dir = os.path.join(stage_root, "package")
        zip_path = os.path.join(stage_root, asset["name"])
        # The manual fallback carries the install's known answers
        # as flags (build .84, issue #75): the fallback gets run by
        # hand exactly where prompts go to die — shells with no
        # usable terminal, the app's own CLI shell first among
        # them — so it must never need to ask a question. Startup
        # comes from the config; voice counts as installed when her
        # venv Python is on disk (the installer still verifies the
        # engines import before it skips the rebuild). The apply
        # job below carries the same two answers.
        fb_cfg = cfg if isinstance(cfg, dict) else {}
        fb_startup = (
            "boot"
            if str(fb_cfg.get("startup") or "on-ui-launch") == "on-boot"
            else "launch")
        fb_voice = (
            "yes"
            if os.path.isfile(os.path.join(
                ROOT, "voice", "venv", "bin", "python"))
            else "no")
        command = (
            "cd " + pkg_dir + " && ./install.sh --startup "
            + fb_startup + " --voice " + fb_voice)
        # Downloading (Build 4 — the refresh-identity repair).
        # A package already downloaded beside the app — including
        # one a pre-.56 Updater refused after downloading — is
        # read back instead of being fetched again ONLY when it
        # is provably the package the feed is offering now: its
        # byte size must equal the feed asset's size. The staging
        # folder is named by the release TAG and the file by the
        # asset name, and both are identical for every
        # publication of one version — so a same-version refresh
        # otherwise finds the PREVIOUS build's zip sitting at
        # this exact path (left there by that build's own apply)
        # and installs those bytes again. That is the Build 2 →
        # Build 3 field failure: the apply ran clean, the
        # checklist passed, and the install still identified as
        # Build 2 afterwards, because the bytes it installed WERE
        # Build 2's — and the version-only confirmation below
        # could not tell the difference. A size mismatch (or a
        # feed that names no size) fetches fresh, overwriting
        # the leftover; the build-identity check in verification
        # is the second lock on the same door, for a leftover
        # whose size happens to match.
        feed_seq = rel.get("buildSeq")
        feed_size = 0
        try:
            feed_size = int(asset.get("size") or 0)
        except Exception:
            feed_size = 0
        _write_update_result(record)
        data = None
        from_disk = False
        if os.path.isfile(zip_path):
            try:
                if feed_size and os.path.getsize(zip_path) == feed_size:
                    with open(zip_path, "rb") as f:
                        data = f.read()
                    from_disk = True
            except Exception as e:
                fail("downloading",
                     "Downloading the update failed: the package "
                     "already beside the app could not be read ("
                     + str(e) + ") — nothing was staged.")
                return
        if data is None:
            try:
                data = github_download(asset["url"])
            except Exception as e:
                fail("downloading",
                     "Downloading the update failed ("
                     + type(e).__name__ + ") — nothing was staged.")
                return
        # Verifying: unwrap a gzip-wrapped payload, then the same
        # Apex-package verification as always — a real zip, holding
        # install.sh + VERSION, with no path escaping its folder —
        # plus the build-identity check (Build 4): when the feed
        # names the target's Build number, the package in hand
        # must BE that build; its bridge.py carries the sequence
        # the installed app will report. A package naming a
        # different build is the wrong bytes, however valid a zip
        # it is. When the wrong bytes came from the leftover
        # beside the app, they are discarded and the offered
        # package is fetched fresh, once, and verified again;
        # when a fresh download itself names the wrong build, the
        # feed and its asset disagree and the apply fails here,
        # in words, with nothing staged.
        record["step"] = "verifying"
        _write_update_result(record)
        retried_fresh = False
        while True:
            payload, _note = _unwrap_package(data)
            if payload is None:
                if _note == "gzip-broken":
                    fail("verifying",
                         "The download arrived gzip-wrapped but "
                         "could not be unwrapped — nothing was "
                         "staged.")
                else:
                    fail("verifying",
                         "The download arrived gzip-wrapped, but "
                         "what is inside is not a zip file — "
                         "nothing was staged.")
                return
            try:
                zf = zipfile.ZipFile(io.BytesIO(payload))
                names = zf.namelist()
            except Exception:
                fail("verifying",
                     "The download did not arrive as a zip file "
                     "— nothing was staged.")
                return
            if "install.sh" not in names or "VERSION" not in names:
                fail("verifying",
                     "That zip is not an Apex package (no "
                     "install.sh / VERSION inside) — nothing was "
                     "staged.")
                return
            base = os.path.realpath(pkg_dir)
            escaped = ""
            for member in names:
                target = os.path.realpath(
                    os.path.join(pkg_dir, member))
                if target != base and not target.startswith(
                        base + os.sep):
                    escaped = member
                    break
            if escaped:
                fail("verifying",
                     "The package zip contains a path outside its "
                     "folder (" + escaped + ") — nothing was "
                     "staged.")
                return
            if feed_seq is not None and "bridge.py" in names:
                pkg_seq = None
                try:
                    with zf.open("bridge.py") as bf:
                        _m = re.search(
                            rb"SHIPPED_BUILD_SEQ\s*=\s*([0-9]+)",
                            bf.read())
                    if _m:
                        pkg_seq = int(_m.group(1))
                except Exception:
                    pkg_seq = None
                if pkg_seq is not None and pkg_seq != feed_seq:
                    if from_disk and not retried_fresh:
                        retried_fresh = True
                        from_disk = False
                        try:
                            data = github_download(asset["url"])
                        except Exception as e:
                            fail("downloading",
                                 "Downloading the update failed ("
                                 + type(e).__name__ + ") — nothing "
                                 "was staged.")
                            return
                        continue
                    fail("verifying",
                         "The package in hand is Build "
                         + str(pkg_seq) + ", but the release on "
                         "offer is Build " + str(feed_seq)
                         + " — not the same bytes, so nothing was "
                         "staged. Check again to fetch the offered "
                         "package.")
                    return
            break
        # Staging: the verified (unwrapped) zip lands beside the
        # app and unpacks under updates/<tag>/package, as before.
        record["step"] = "staging"
        _write_update_result(record)
        try:
            os.makedirs(pkg_dir, exist_ok=True)
            with open(zip_path, "wb") as f:
                f.write(payload)
            zf.extractall(pkg_dir)
            try:
                os.chmod(os.path.join(pkg_dir, "install.sh"), 0o755)
            except Exception:
                pass
        except Exception as e:
            fail("staging", "Staging the download failed: " + str(e))
            return
        staged["dir"] = pkg_dir
        staged["command"] = command
        record["stagedDir"] = pkg_dir
        record["command"] = command
        record["step"] = "installing"
        _write_update_result(record)
        # Installing + restarting belong to the detached helper:
        # the installer stops this bridge, so the bridge cannot
        # run it and live to tell the panel. The helper outlives
        # the swap, relaunches the app, and finishes the record.
        try:
            cfg_now = cfg if isinstance(cfg, dict) else load_config()
            job = {
                "root": ROOT,
                "pkgDir": pkg_dir,
                "tagDir": tag_dir,
                "resultPath": UPDATE_RESULT_PATH,
                "installLog": os.path.join(
                    stage_root, "apply-install.log"),
                "relaunchLog": os.path.join(
                    stage_root, "apply-relaunch.log"),
                # Build 5: the helper's step log — written from
                # its first instruction, beside the job, with its
                # path carried on the apply record so the panel,
                # the watchdog, and anyone reading the wreckage
                # afterwards can find the last step it completed.
                "traceLog": os.path.join(
                    stage_root, "apply-trace.log"),
                "command": command,
                "port": BRIDGE_PORT,
                "startup": str(cfg_now.get("startup") or "on-ui-launch"),
                "voice": fb_voice,
                "targetTuple": list(_version_tuple(tag)),
                # Build 4: the target's Build number, when the
                # feed names one — the helper's confirmation must
                # observe THIS landing, not just the version
                # number a refresh shares with its predecessor.
                "targetBuildSeq": rel.get("buildSeq"),
                "targetLabel": record["targetLabel"],
                # Build 3: the label the finished record carries
                # for the to-side — composed here, where the
                # target's Build number is known (for a refresh
                # it is "Build <n>", which the helper cannot
                # derive from the VERSION file it confirms
                # against; the plain version label otherwise).
                "afterLabel": record["targetLabel"],
            }
            job_path = os.path.join(stage_root, "apply-job.json")
            helper_path = os.path.join(stage_root, "apply-helper.py")
            with open(job_path, "w") as f:
                json.dump(job, f)
            with open(helper_path, "w") as f:
                f.write(APPLY_HELPER_PY)
            os.chmod(helper_path, 0o755)
            logf = open(os.path.join(stage_root, "apply.log"), "ab")
            try:
                proc = subprocess.Popen(
                    [sys.executable, helper_path, job_path],
                    cwd=stage_root, stdin=subprocess.DEVNULL,
                    stdout=logf, stderr=subprocess.STDOUT,
                    start_new_session=True, close_fds=True)
            finally:
                logf.close()
            record["helperPid"] = proc.pid
            record["traceLog"] = job["traceLog"]
            _write_update_result(record)
        except Exception as e:
            fail("install",
                 "The update was staged but the install could not "
                 "be started: " + str(e) + " The staged package is "
                 "still in place — the manual fallback below "
                 "finishes the job by hand.")
            return
    except Exception as e:
        # Last resort: never leave the record claiming a step is
        # still running when this worker has died.
        try:
            record["state"] = "failed"
            record["error"] = "The update failed: " + str(e)
            record["failedAt"] = _now_iso()
            _write_update_result(record)
        except Exception:
            pass
    finally:
        _update_apply_state["running"] = False


def update_apply_payload(cfg=None):
    # Starts the end-to-end apply (see the section comment) and
    # answers at once: progress and outcome live in the update
    # record, which GET /api/update/result serves and the panel
    # polls. A second apply while one is already working — this
    # bridge's worker, or the detached helper a previous click
    # left installing — is refused in words, never queued.
    rec = update_result_payload()
    helper_alive = False
    if rec.get("state") == "working" and rec.get("helperPid"):
        try:
            helper_alive = pid_alive(int(rec["helperPid"]))
        except Exception:
            helper_alive = False
    with _update_apply_lock:
        if _update_apply_state["running"] or helper_alive:
            return {"ok": False, "error": "An update is already "
                    "being applied — watch its progress in the "
                    "Updater; it finishes (or fails) on its own."}
        _update_apply_state["running"] = True
    t = threading.Thread(
        target=_run_update_apply, args=(cfg,), daemon=True)
    t.start()
    return {"ok": True, "started": True}


def save_download_payload(data):
    # The dashboard's download-save flow (build .48, issue #10):
    # inside the desktop shell the webview cannot save a file the
    # way a browser does, so when the operator clicks a download
    # there (a chip .png, an export ZIP) the dashboard fetches the
    # bytes itself and hands them here as base64; the bridge writes
    # them into the operator's Downloads folder. The filename is
    # never trusted as a path: it is reduced to a plain basename,
    # a name already taken gains a numeric suffix instead of an
    # overwrite, and anything over the cap is refused outright.
    name = str(data.get("filename") or "").strip()
    name = name.replace(chr(92), "/").split("/")[-1].strip()
    if name in ("", ".", ".."):
        name = "navi-download"
    try:
        blob = base64.b64decode(str(data.get("dataBase64") or ""),
                                validate=True)
    except Exception:
        return {"ok": False, "error": "That download did not arrive "
                "as readable data — nothing was saved."}
    if len(blob) > 64 * 1024 * 1024:
        return {"ok": False, "error": "That file is larger than the "
                "64 MB download limit — nothing was saved."}
    try:
        folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, name)
        if os.path.exists(target):
            stem, dot, ext = name.rpartition(".")
            n = 2
            while os.path.exists(target):
                if stem and dot:
                    candidate = stem + " (" + str(n) + ")." + ext
                else:
                    candidate = name + " (" + str(n) + ")"
                target = os.path.join(folder, candidate)
                n += 1
        with open(target, "wb") as f:
            f.write(blob)
    except Exception as e:
        return {"ok": False, "error": "Saving to the Downloads "
                "folder failed: " + str(e)}
    return {"ok": True, "path": target, "sizeBytes": len(blob)}


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
#   mesh-cards/         own.png — this node's pairing-card picture,
#                       minted fresh at backup time — plus one
#                       peer-<node>.png per paired peer, re-drawn
#                       from the stored card (the payload is the
#                       card, so a restored picture imports whole).
#                       The node keypair is never among them.
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
GITHUB_BACKUP_ITEMS = ["soul", "memory", "settings", "chips", "rag", "workflows", "vault", "mesh-cards"]
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


def github_api_raw(method, url, token, data, content_type):
    # github_api's sibling for binary bodies (release assets ride
    # the uploads host as raw bytes, not JSON). Same contract:
    # (status, parsed JSON or text), never raises for HTTP errors.
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "navi-apex-bridge",
        "Content-Type": content_type,
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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
            return {
                "token": str(data["token"]),
                "login": str(data.get("login") or ""),
                "refresh_token": str(data.get("refresh_token") or ""),
                "expires_in": data.get("expires_in"),
            }
    except Exception:
        pass
    return None


def github_save_auth(token, login, refresh_token=None, expires_in=None):
    # The whole token set GitHub returned. An expiring user token
    # also carries a refresh token and a lifetime; the first build
    # threw both away, so the day the access token expired every
    # authenticated call answered 401 forever, with no renewal
    # path (issue #14). A non-expiring sign-in returns neither and
    # stores exactly what it always stored.
    data = {"token": token, "login": login}
    if refresh_token:
        data["refresh_token"] = str(refresh_token)
    if expires_in:
        data["expires_in"] = expires_in
    os.makedirs(os.path.dirname(GITHUB_TOKEN_PATH), exist_ok=True)
    fd = os.open(GITHUB_TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    try:
        os.chmod(GITHUB_TOKEN_PATH, 0o600)
    except Exception:
        pass


def github_refresh_auth():
    # Renew an expired access token from the stored refresh token
    # — once. Returns the fresh auth dict (already saved), or None
    # when there is nothing to renew with or GitHub refuses; the
    # caller then asks the operator to sign in again.
    auth = github_auth()
    if not auth or not auth.get("refresh_token"):
        return None
    client_id = github_settings(load_config())["client_id"]
    if not client_id:
        return None
    st, resp = github_api(
        "POST", "https://github.com/login/oauth/access_token", None,
        {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": auth["refresh_token"],
        },
        form=True,
    )
    if isinstance(resp, dict) and resp.get("access_token"):
        # GitHub rotates the refresh token on renewal: keep the
        # new one when it sends one, the stored one otherwise.
        github_save_auth(
            str(resp["access_token"]),
            auth["login"],
            resp.get("refresh_token") or auth["refresh_token"],
            resp.get("expires_in"),
        )
        return github_auth()
    return None


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
        # Keep the whole token set: when GitHub answers with an
        # expiring token, the refresh token and lifetime ride
        # along — without them the sign-in dies with the access
        # token and cannot be renewed (issue #14).
        github_save_auth(token, login, resp.get("refresh_token"), resp.get("expires_in"))
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
    # The Mesh ledger rides a backup ONLY on the operator's
    # explicit tick (Settings → System → Navi Mesh; Q4, off by
    # default): it is metadata — who lent whom how many seconds —
    # but whose machines talked is the operator's business, so it
    # stays home unless they say otherwise. The node keypair never
    # rides a backup, tick or no tick.
    if mesh_settings(cfg)["ledgerInBackup"] and os.path.isfile(MESH_LEDGER_PATH):
        with open(MESH_LEDGER_PATH, "rb") as f:
            files["mesh/ledger.jsonl"] = f.read()
    # Mesh pairing cards (Build 9, #89): the pictures themselves,
    # on their own essential's tick. This node's own card is
    # minted fresh from the live card; each paired peer's picture
    # is re-drawn from its stored card (build_mesh_peer_card_png)
    # — the payload is the card, so a restored picture imports
    # whole. The node keypair is NOT a card and never rides: only
    # the public card data crosses, exactly what a pairing hands
    # to another machine in the open.
    if "mesh-cards" in items:
        if mesh_node_id() and mesh_cert_fingerprint():
            try:
                files["mesh-cards/own.png"] = build_mesh_card_png(cfg)
            except Exception:
                pass
        mesh_block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
        borrow_block = mesh_block.get("borrow") if isinstance(mesh_block.get("borrow"), dict) else {}
        for peer in borrow_block.get("peers") or []:
            if not isinstance(peer, dict):
                continue
            node_id = str(peer.get("nodeId") or "")
            if len(node_id) != 64:
                continue
            try:
                files["mesh-cards/peer-" + node_id[:12] + ".png"] = build_mesh_peer_card_png(peer)
            except Exception:
                continue
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
    if "vault" in items and os.path.isdir(VAULT_DIR):
        for base, dirs, names in os.walk(VAULT_DIR):
            dirs.sort()
            for name in sorted(names):
                fpath = os.path.join(base, name)
                if os.path.isfile(fpath):
                    rel = os.path.relpath(fpath, VAULT_DIR).replace(os.sep, "/")
                    with open(fpath, "rb") as f:
                        files["vault/" + rel] = f.read()
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
    # The manifest records the backup's file count — the files the
    # backup actually contains, exactly as Settings → GitHub & Backup
    # presents them: one per ticked essential's payload files. The
    # manifest itself (navi-backup.json) is the index, not content,
    # and is never counted — counting it (plus expanding settings
    # into three files) is what pinned the old readout at "6 files"
    # no matter what was ticked. The status column's simple
    # "# files | # days ago" readout and Settings → GitHub & Backup
    # both read this one record, so they can never disagree.
    manifest["fileCount"] = len(files)
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
            "description": "Apex backup — her ready-to-fly essentials (Soul, Memory, settings, chips, RAG packs, workflows, the Vault, Mesh pairing cards).",
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
        if path in fixed or path.startswith("rag-packs/") or path.startswith("vault/") or path.startswith("mesh-cards/") or (path.startswith("chips/") and path.endswith(".png")):
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
        "vault": "The Vault",
        "mesh-cards": "Mesh pairing cards",
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
    if "vault" in items:
        backed_paths = sorted(p for p in files if p.startswith("vault/"))
        cur_paths = []
        if os.path.isdir(VAULT_DIR):
            for base, dirs, names in os.walk(VAULT_DIR):
                for name in names:
                    cur_paths.append("vault/" + os.path.relpath(os.path.join(base, name), VAULT_DIR).replace(os.sep, "/"))
        changes.append({
            "item": "vault", "label": labels["vault"],
            "detail": "Would restore " + str(len(backed_paths)) + " vault notes from the backup — the whole shared desk. This machine currently holds " + str(len(cur_paths)) + ".",
            "willChange": backed_paths != sorted(cur_paths),
        })
    if "mesh-cards" in items:
        backed_peers = sorted(p for p in files if p.startswith("mesh-cards/peer-") and p.endswith(".png"))
        backed_ids = sorted(os.path.basename(p)[5:-4] for p in backed_peers)
        mesh_block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
        borrow_block = mesh_block.get("borrow") if isinstance(mesh_block.get("borrow"), dict) else {}
        cur_ids = sorted(str(p.get("nodeId") or "")[:12] for p in (borrow_block.get("peers") or []) if isinstance(p, dict))
        own_backed = "mesh-cards/own.png" in files
        own_here = os.path.isfile(os.path.join(MESH_CARDS_DIR, "own.png"))
        changes.append({
            "item": "mesh-cards", "label": labels["mesh-cards"],
            "detail": "Would restore " + str(len(backed_peers)) + " peer pairing-card picture(s) to config/mesh/cards/ and re-pair those peers through the normal card check" + ("; the backup also holds this machine's own card picture, kept as a file — it never replaces the identity of the machine restoring" if own_backed else "") + ". This machine is currently paired with " + str(len(cur_ids)) + ".",
            "willChange": backed_ids != cur_ids or (own_backed and not own_here),
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
    if "vault" in items:
        wrote = False
        for path, data in files.items():
            if path.startswith("vault/"):
                rel = vault_join(path[len("vault/"):])
                if rel:
                    full = os.path.join(VAULT_DIR, *rel.split("/"))
                    os.makedirs(os.path.dirname(full), exist_ok=True)
                    with open(full, "wb") as f:
                        f.write(data)
                    wrote = True
        if wrote:
            applied.append("The Vault")
    if "mesh-cards" in items:
        wrote = False
        fresh_cfg = load_config()
        for path in sorted(files):
            if not path.startswith("mesh-cards/") or not path.endswith(".png"):
                continue
            base = os.path.basename(path)
            if not _github_safe_part(base):
                continue
            os.makedirs(MESH_CARDS_DIR, exist_ok=True)
            with open(os.path.join(MESH_CARDS_DIR, base), "wb") as f:
                f.write(files[path])
            wrote = True
            if base.startswith("peer-"):
                # Peers come back through the SAME validation a
                # hand import passes — picture parsed, card
                # checked, record added by mesh_add_peer. A
                # picture that fails the check stays a file in the
                # cards folder and pairs nothing. This machine's
                # own card picture (own.png) is never imported: it
                # describes the machine the backup came FROM, and
                # restoring must not overwrite a live identity.
                peer, _perr = parse_mesh_card_png(files[path])
                if peer is not None:
                    mesh_add_peer(fresh_cfg, peer)
        if wrote:
            applied.append("Mesh pairing cards")
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
    # Build .86 (issue #79): the walk is RECURSIVE — a legacy chip
    # keeps its code in a package directory (app_cryptex/ and kin),
    # and a root-only listing never sees it, which is how a chip
    # could "install" and never run. Every file in the tree is
    # listed with its repo-relative path; package directories keep
    # their paths in the payload file set.
    entries = []

    def _walk(dir_path):
        url = (
            "https://api.github.com/repos/" + full + "/contents"
            + ("/" + dir_path if dir_path else "")
            + "?ref=" + urllib.parse.quote(ref, safe="")
        )
        listing = github_json(url)
        if not isinstance(listing, list):
            raise ValueError("GitHub did not return the repo's file list.")
        for item in listing:
            p = str(item.get("path") or "")
            if item.get("type") == "dir":
                _walk(p)
            elif item.get("type") == "file":
                entries.append((p, item))

    _walk("")
    pys = [(p, i) for (p, i) in entries if p.lower().endswith(".py")]
    if not pys:
        raise ValueError(
            "the repo has no Python chip file at " + ref
            + " — a navi-chips repo carries its chip as a .py file."
        )
    # A navi-chip.json manifest at the repo root (written by the
    # GitHub-ready export) names the entry file outright and
    # carries the chip's description and declared output.
    manifest = {}
    man_item = next(
        (i for (p, i) in entries if p == "navi-chip.json"),
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
    pick_path = ""
    for want in wants:
        for (p, i) in pys:
            if p.lower() == want or p.lower().rsplit("/", 1)[-1] == want:
                pick = i
                pick_path = p
                break
        if pick:
            break
    if pick is None and len(pys) == 1:
        pick_path, pick = pys[0]
    if pick is None:
        names = ", ".join(p for (p, _i) in pys)
        raise ValueError(
            "the repo holds several Python files (" + names
            + ") and none is the chip's entry — name the entry file "
            "root.py, or add a navi-chip.json manifest naming it."
        )
    # Every Python file in the tree comes down at its relative
    # path: the entry becomes the chip's code and the rest ride
    # along as its importable modules and packages, so a
    # multi-file or package chip runs exactly as authored.
    files = []
    code = ""
    for (p, item) in pys:
        text = github_download(item["download_url"]).decode("utf-8", "replace")
        if item is pick:
            code = text
        else:
            files.append({"path": p, "content": text[:200000]})
    if not code.strip():
        raise ValueError(pick_path + " is empty.")
    # Declared dependencies ride along as data (issue #79): a
    # chip-requirements.txt at the repo root is read and its lines
    # are stored on the payload — surfaced on the chip's card,
    # never installed automatically.
    requirements = []
    req_item = next((i for (p, i) in entries if p == "chip-requirements.txt"), None)
    if req_item is not None:
        try:
            req_text = github_download(req_item["download_url"]).decode("utf-8", "replace")
            requirements = [
                ln.strip() for ln in req_text.splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ][:50]
        except Exception:
            requirements = []
    payload = {
        "name": repo["name"],
        "description": str(manifest.get("description") or repo["description"] or ""),
        "code": code[:200000],
        "output": str(manifest.get("output") or ""),
        "requirements": requirements,
        "glyph": str(manifest.get("glyph") or ""),
        # Issue #99: the manifest's version rides inside the
        # picture, the way its glyph already does.
        "version": str(manifest.get("version") or ""),
        "files": _valid_chip_files(
            [{"path": "root.py", "content": code[:200000]}] + files,
            code[:200000],
        ),
    }
    return payload, pick_path


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
    # Issue #22: an entry also reads as installed when a chip with
    # the same slug is on this machine under another name — a
    # Studio-forged chip (its local/ record), the same repo
    # installed from a different owner, or a .png dropped into
    # chips/ by hand (no record at all). An exact full-name match
    # keeps the update math; a slug match claims only "installed"
    # — no update is offered against a lineage this machine did
    # not download from this repo.
    installs_ci = {}
    by_slug = {}
    for row in load_chip_installs():
        fn = row.get("full_name") or ""
        if fn:
            installs_ci.setdefault(fn.lower(), row)
        s = fn.split("/")[-1].lower()
        if s and s not in by_slug:
            by_slug[s] = row
    local_files = {}
    for lc in local_chips():
        local_files.setdefault(str(lc.get("slug") or "").lower(), lc.get("file"))
    chips = []
    for repo in repos:
        inst = installs.get(repo["fullName"]) or installs_ci.get(repo["fullName"].lower())
        slug_row = None
        slug_file = None
        if not inst:
            s = repo["fullName"].split("/")[-1].lower()
            slug_row = by_slug.get(s)
            slug_file = local_files.get(s)
        matched = inst or slug_row
        slug_matched = bool(not inst and (slug_row is not None or slug_file is not None))
        update = False
        if inst:
            if repo["latestRelease"]:
                update = inst.get("installed_tag") != repo["latestRelease"]["tag"]
            else:
                update = bool(
                    inst.get("installed_pushed_at")
                    and repo["pushedAt"] > inst["installed_pushed_at"]
                )
        if inst:
            ref = _display_ref(inst.get("installed_ref"))
        elif slug_row and str(slug_row.get("full_name") or "").startswith("local/"):
            ref = _display_ref(slug_row.get("installed_ref"))
        else:
            ref = None
        entry = dict(repo)
        entry["inCatalog"] = True
        entry["installed"] = bool(inst) or slug_matched
        entry["slugMatched"] = slug_matched
        entry["installedTag"] = matched.get("installed_tag") if matched else None
        entry["installedRef"] = ref
        entry["installedAt"] = matched.get("installed_at") if matched else None
        entry["updateAvailable"] = update
        entry["localFile"] = (matched.get("local_file") if matched else None) or slug_file
        entry["locallyEdited"] = bool(matched.get("locally_edited")) if matched else False
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
            "inCatalog": False, "installed": True, "slugMatched": False,
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


# --- Cartridge faces (0.1.9e, issue #92 graphics pass) --------------
# A chip's face is DRAWN, not rolled: one chunky pixel glyph that
# means the chip's function, on the family shell — black body, coral
# notched bands top and bottom. The glyph is named in the chip's
# metadata ("glyph" in the payload, and in navi-chip.json at export):
# an explicit glyph wins; otherwise a keyword heuristic over the
# chip's name and description picks one; a chip nothing claims keeps
# the legacy name-seeded pattern face, which remains only as that
# fallback. Faces are minted at forge time — installed and published
# pictures are never rewritten.
GLYPH_PIXELS = {
    "key": [
        ".####.......",
        "#....#......",
        "#....#......",
        ".####.#####.",
        "......#..#..",
        "......#..##.",
        "......#.....",
        "......#.....",
        "......#.....",
        "............",
        "............",
        "............",
    ],
    "lock": [
        "....####....",
        "...#....#...",
        "...#....#...",
        "...#....#...",
        "..########..",
        "..########..",
        "..###..###..",
        "..###..###..",
        "..########..",
        "..########..",
        "............",
        "............",
    ],
    "hash": [
        "............",
        "...#..#.....",
        "...#..#.....",
        ".#########..",
        "...#..#.....",
        "...#..#.....",
        ".#########..",
        "...#..#.....",
        "...#..#.....",
        "............",
        "............",
        "............",
    ],
    "text": [
        ".##########.",
        ".#........#.",
        ".#.######.#.",
        ".#........#.",
        ".#.######.#.",
        ".#........#.",
        ".#.####...#.",
        ".#........#.",
        ".##########.",
        "............",
        "............",
        "............",
    ],
    "swap": [
        "............",
        "....#####...",
        "...#....##..",
        "..#########.",
        "...#....##..",
        "....#####...",
        "....#####...",
        "...##....#..",
        "..#########.",
        "...##....#..",
        "....#####...",
        "............",
    ],
    "gear": [
        "............",
        ".....##.....",
        "..#..##..#..",
        "..#.####.#..",
        "....####....",
        ".##########.",
        ".##########.",
        "....####....",
        "..#.####.#..",
        "..#..##..#..",
        ".....##.....",
        "............",
    ],
    "network": [
        ".....##.....",
        "....#..#....",
        "....#..#....",
        ".....##.....",
        "....#..#....",
        "...#....#...",
        "..#......#..",
        ".#........#.",
        "#..#....#..#",
        "#..#....#..#",
        ".##......##.",
        "............",
    ],
    "image": [
        ".##########.",
        ".#........#.",
        ".#..#.....#.",
        ".#.###....#.",
        ".#.#####..#.",
        ".##########.",
        ".#......###.",
        ".#....#####.",
        ".#..#######.",
        ".##########.",
        "............",
        "............",
    ],
    "music": [
        "........##..",
        ".......#..#.",
        ".......#...#",
        ".......#....",
        ".......#....",
        "......##....",
        ".....####...",
        "....######..",
        "....######..",
        ".....####...",
        "............",
        "............",
    ],
    "dice": [
        "............",
        ".##########.",
        ".##########.",
        ".##......##.",
        ".##..##..##.",
        ".##..##..##.",
        ".##......##.",
        ".##..##..##.",
        ".##..##..##.",
        ".##########.",
        ".##########.",
        "............",
    ],
    "book": [
        "............",
        ".#........#.",
        ".##......##.",
        ".#.#....#.#.",
        ".#..#..#..#.",
        ".#..#..#..#.",
        ".#...##...#.",
        ".#........#.",
        ".#........#.",
        "..########..",
        "............",
        "............",
    ],
    "terminal": [
        "............",
        ".##########.",
        ".#........#.",
        ".#.##.....#.",
        ".#..##....#.",
        ".#.##.....#.",
        ".#......###.",
        ".#........#.",
        ".##########.",
        "............",
        "............",
        "............",
    ],
    "shield": [
        "............",
        "..########..",
        "..########..",
        "..##....##..",
        "..##....##..",
        "...#....#...",
        "...#.##.#...",
        "....####....",
        ".....##.....",
        ".....##.....",
        "......#.....",
        "............",
    ],
    "clock": [
        "............",
        "....####....",
        "..##....##..",
        "..#......#..",
        "..#..#...#..",
        "..#..##..#..",
        "..#......#..",
        "..#......#..",
        "..##....##..",
        "....####....",
        "............",
        "............",
    ],
    "chart": [
        "............",
        "............",
        ".......#....",
        ".......#....",
        "...#...#....",
        "...#...#.#..",
        "...#...###..",
        ".#.#...###..",
        ".###...###..",
        ".#########..",
        ".#########..",
        "............",
    ],
    "star": [
        "............",
        ".....#......",
        ".....#......",
        "....###.....",
        ".#########..",
        "..#######...",
        "...#####....",
        "....###.....",
        "...##.##....",
        "...#...#....",
        "..#.....#...",
        "............",
    ],
}

_GLYPH_KEYWORDS = [
    ("key", ("cryptex", "cipher", "encrypt", "decrypt", "encode", "decode", "key")),
    ("hash", ("hash", "md5", "sha1", "sha256", "sha512", "digest")),
    ("lock", ("password", "vault", "lock", "secret")),
    ("swap", ("translate", "convert", "swap", "exchange")),
    ("music", ("music", "audio", "song", "sound", "play")),
    ("image", ("image", "photo", "picture", "camera")),
    ("dice", ("dice", "random", "game", "fun", "joke")),
    ("book", ("book", "knowledge", "docs", "read", "library")),
    ("network", ("mesh", "network", "net", "peer", "sync")),
    ("shield", ("scan", "security", "shield", "guard", "nmap", "vuln")),
    ("terminal", ("shell", "terminal", "command", "cli", "exec")),
    ("clock", ("clock", "time", "schedule", "timer", "alarm")),
    ("chart", ("chart", "stats", "graph", "metric", "report")),
    ("text", ("text", "word", "string", "note", "write")),
    ("gear", ("tool", "config", "setting", "util")),
    ("star", ("oracle", "fortune", "magic", "star")),
]


def pick_chip_glyph(payload):
    # The face a payload earns: its own declared glyph first, then
    # the keyword heuristic over name + description, else None —
    # and None is what keeps the legacy seeded face.
    g = str((payload or {}).get("glyph") or "").strip().lower()
    if g in GLYPH_PIXELS:
        return g
    hay = (
        str((payload or {}).get("name") or "")
        + " "
        + str((payload or {}).get("description") or "")
    ).lower()
    for name, words in _GLYPH_KEYWORDS:
        if any(w in hay for w in words):
            return name
    return None


def _cartridge_face_png(payload, keyword):
    # The card-grade family face (0.1.9e Build 2): the cartridge
    # drawn with the Mesh pairing cards' machinery — the same
    # block font, pixel buffer, and PNG assembly — at card
    # resolution in the classic portrait stance, 528x616 (the old
    # 96x112 face at 5.5x, same proportions). Family DNA intact:
    # black shell, rim, coral notched bands top and bottom as the
    # cartridge's contacts (notches on the bands' inner edges),
    # one drawn glyph large in its window, then the thing's name,
    # its use line, and honest small print. A chip no glyph claims
    # keeps the legacy name-seeded pattern, drawn in the window at
    # the same grade. Faces are minted at forge time — installed
    # and published pictures are never rewritten.
    W, H = 528, 616
    BG = (10, 14, 18)
    SHELL = (8, 9, 11)
    RIM = (34, 48, 61)
    CORAL = (255, 111, 97)
    WINDOW = (14, 17, 21)
    INK = (230, 241, 245)
    DIM = (159, 179, 200)
    img = bytearray(bytes(SHELL) * (W * H))

    def px(x, y, rgb):
        if 0 <= x < W and 0 <= y < H:
            o = (y * W + x) * 3
            img[o] = rgb[0]
            img[o + 1] = rgb[1]
            img[o + 2] = rgb[2]

    def rect(x0, y0, x1, y1, rgb):
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                px(xx, yy, rgb)

    for i in range(4):
        for x in range(W):
            px(x, i, RIM)
            px(x, H - 1 - i, RIM)
        for y in range(H):
            px(i, y, RIM)
            px(W - 1 - i, y, RIM)

    BAND_H = 26
    TOP_BAND_Y = 24
    BOT_BAND_Y = H - 24 - BAND_H

    def band(y0, notch_first):
        # A coral contact band; along its inner edge a stepped
        # bite is taken out of every second cell — the notches
        # the small face drew, at card scale.
        rect(4, y0, W - 4, y0 + BAND_H, CORAL)
        for x in range(4, W - 4):
            if (x // 44) % 2 == 0:
                for yy in notch_first:
                    px(x, yy, SHELL)

    band(TOP_BAND_Y, (TOP_BAND_Y + BAND_H - 2, TOP_BAND_Y + BAND_H - 1))
    band(BOT_BAND_Y, (BOT_BAND_Y, BOT_BAND_Y + 1))

    MX = 40
    if keyword == "navi-rag":
        head_l, head_r = "KNOWLEDGE", "NAVI-RAG"
    else:
        head_l, head_r = "APEX CHIP", "NAVI-CHIPS"
    y = TOP_BAND_Y + BAND_H + 22
    _mesh_face_draw(img, W, H, MX, y, head_l, 3, CORAL)
    _mesh_face_draw(
        img, W, H, W - MX - _mesh_face_text_w(head_r, 3), y, head_r, 3, DIM
    )
    y += 21 + 22

    # The glyph window: rim-framed, dark inside, one drawn glyph
    # large — or the legacy seeded pattern for a chip (never a
    # knowledge cartridge) that no glyph claims.
    WIN = 300
    wx = (W - WIN) // 2
    wy = y
    rect(wx - 6, wy - 6, wx + WIN + 6, wy + WIN + 6, RIM)
    rect(wx, wy, wx + WIN, wy + WIN, WINDOW)
    glyph = pick_chip_glyph(payload) if keyword != "navi-rag" else "book"
    if glyph is not None and glyph in GLYPH_PIXELS:
        grid = GLYPH_PIXELS[glyph]
        cell = WIN // 12
        for cy in range(12):
            for cx in range(12):
                if grid[cy][cx] == "#":
                    rect(
                        wx + cx * cell, wy + cy * cell,
                        wx + (cx + 1) * cell, wy + (cy + 1) * cell,
                        CORAL,
                    )
    else:
        palette = [
            (34, 211, 238), (245, 181, 68), (52, 211, 153),
            (248, 113, 113), (167, 139, 250),
        ]
        h = 0
        seed = 7
        for ch in str(payload.get("name") or ""):
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
            seed = (seed * 31 + ord(ch)) & 0xFFFFFFFF
        accent = palette[h % len(palette)]
        blocks = []
        for _ in range(64):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            blocks.append(seed / 0x7FFFFFFF > 0.55)
        pad = 24
        cell = (WIN - 2 * pad) / 8.0
        for by in range(8):
            for bx in range(8):
                if blocks[by * 8 + bx]:
                    rect(
                        int(wx + pad + bx * cell), int(wy + pad + by * cell),
                        int(wx + pad + (bx + 1) * cell),
                        int(wy + pad + (by + 1) * cell),
                        accent,
                    )
                else:
                    rect(
                        int(wx + pad + bx * cell), int(wy + pad + by * cell),
                        int(wx + pad + (bx + 1) * cell),
                        int(wy + pad + (by + 1) * cell),
                        BG,
                    )
    y = wy + WIN + 24

    # The name band: auto-fitting like the Mesh cards' name —
    # start big, shrink until it fits, truncate only at the floor.
    name = _mesh_face_clean(payload.get("name") or "") or (
        "KNOWLEDGE PACK" if keyword == "navi-rag" else "CHIP"
    )
    scale = 7
    while scale > 2 and _mesh_face_text_w(name, scale) > W - 2 * MX:
        scale -= 1
    if _mesh_face_text_w(name, scale) > W - 2 * MX:
        name = name[: max(0, (W - 2 * MX) // (6 * scale) - 3)] + "..."
    _mesh_face_draw(img, W, H, MX, y, name, scale, INK)
    y += 7 * scale + 16

    # The use line: the description, wrapped at the width that
    # fits scale 2, up to three lines.
    max_chars = (W - 2 * MX) // (6 * 2)
    use = _mesh_face_wrap(
        _mesh_face_clean(payload.get("description") or ""), max_chars
    )
    for line in use[:3]:
        if y + 14 > BOT_BAND_Y - 44:
            break
        _mesh_face_draw(img, W, H, MX, y, line, 2, DIM)
        y += 14 + 8

    # Footer small print, above the bottom band with clearance:
    # the version when the picture's own data knows it (never
    # invented), the output kind, and the family mark. A
    # knowledge cartridge's footer carries its version and its
    # document count instead.
    foot_bits = []
    ver = str(payload.get("version") or "").strip()
    if ver:
        foot_bits.append("V" + ver.upper())
    if keyword == "navi-rag":
        docs = payload.get("documents")
        if isinstance(docs, list):
            foot_bits.append(
                str(len(docs)) + (" DOCUMENT" if len(docs) == 1 else " DOCUMENTS")
            )
        foot_bits.append("NAVI-RAG")
    else:
        # The output KIND, not the output text: a chip whose
        # run() produces text wears TEXT; one that only declares
        # an output wears the first words of it (the way a
        # Mesh card reads its offer).
        if str(payload.get("code") or "").strip():
            foot_bits.append("TEXT")
        else:
            out_line = _mesh_face_clean(payload.get("output") or "")
            if out_line:
                foot_bits.append(out_line[:18])
        foot_bits.append("NAVI-CHIPS")
    foot = _mesh_face_clean(" - ".join(foot_bits))
    while foot and _mesh_face_text_w(foot, 2) > W - 2 * MX:
        foot = foot[:-1]
    _mesh_face_draw(img, W, H, MX, BOT_BAND_Y - 14 - 16, foot, 2, DIM)

    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += img[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _png_chunk(b"IEND", b"")
    )


def build_cartridge_png(payload):
    # The PICO-8 trick in Battle Network dress: the visible image is
    # a battle-chip label; the chip's whole codebase rides inside the
    # PNG in a tEXt chunk (keyword "navi-chip", JSON payload).
    face = _cartridge_face_png(payload, "navi-chip")
    text = b"navi-chip\x00" + json.dumps(payload).encode()
    # Rebuild with the payload chunk ahead of the image data.
    ihdr_end = 8 + 12 + 13
    return (
        face[:ihdr_end]
        + _png_chunk(b"tEXt", text)
        + face[ihdr_end:]
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
                        "glyph": str(payload.get("glyph") or ""),
                        # Issue #99: the version the picture itself
                        # carries (Build 2 and later forges); older
                        # pictures simply have none — "" here, and
                        # no surface invents one for them.
                        "version": str(payload.get("version") or ""),
                    }
                return None
        if kind == b"IEND":
            break
        pos += 8 + length + 4
    return None


def deck_contents(cfg):
    # Everything that rides a picture, for ChipDeck (0.1.9e, #94):
    # installed chips, the Mesh pairing cards on disk, and the
    # knowledge packs (each pack's cartridge is built on demand by
    # /api/rag/cartridge.png). State is read from the same stores
    # the owning pages read — the Deck is a view, not a store.
    chips = [
        {
            "file": c["file"], "name": c["name"],
            "description": c.get("description") or "",
            "glyph": pick_chip_glyph(c) or "",
            # Issue #99: the version the picture itself carries —
            # "" for pictures forged before it was carried, and
            # the Deck shows nothing rather than a guess for them.
            "version": str(c.get("version") or ""),
            "source": c.get("source"), "sourceKey": c.get("sourceKey"),
            "locallyEdited": bool(c.get("locallyEdited")),
            "unreadable": bool(c.get("unreadable")),
        }
        for c in local_chips()
    ]
    cards = []
    try:
        ms = mesh_settings(cfg)
        paired_ids = {
            str(p.get("nodeId") or "")
            for p in (ms["borrow"]["peers"] or [])
            if isinstance(p, dict)
        }
    except Exception:
        paired_ids = set()
    try:
        card_files = sorted(os.listdir(MESH_CARDS_DIR))
    except Exception:
        card_files = []
    for fn in card_files:
        if not fn.lower().endswith(".png"):
            continue
        entry = {"file": fn, "name": fn[:-4], "nodeId": "", "own": fn == "own.png", "paired": False}
        try:
            with open(os.path.join(MESH_CARDS_DIR, fn), "rb") as f:
                peer, _e = parse_mesh_card_png(f.read())
            if peer is not None:
                entry["name"] = peer.get("name") or entry["name"]
                entry["nodeId"] = str(peer.get("nodeId") or "")
                entry["paired"] = entry["nodeId"] in paired_ids
        except Exception:
            pass
        cards.append(entry)
    packs = [
        {
            "slug": p["slug"], "name": p["name"],
            "description": p.get("description") or "",
            "fullName": p["fullName"], "active": bool(p["active"]),
            "docCount": p["docCount"],
        }
        for p in local_rag_packs()
    ]
    return {"chips": chips, "meshCards": cards, "ragPacks": packs}


def _png_text_keywords(data):
    keys = []
    if not isinstance(data, (bytes, bytearray)) or len(data) < 8 or bytes(data[:8]) != b"\x89PNG\r\n\x1a\n":
        return keys
    pos = 8
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            break
        if kind == b"tEXt":
            chunk_data = data[pos + 8:pos + 8 + length]
            nul = chunk_data.find(b"\x00")
            if nul > 0:
                keys.append(chunk_data[:nul].decode("utf-8", "replace"))
        if kind == b"IEND":
            break
        pos += 8 + length + 4
    return keys


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
        rec = by_file.get(fn)
        full = (rec or {}).get("full_name") or ""
        try:
            with open(os.path.join(CHIPS_DIR, fn), "rb") as f:
                payload = parse_cartridge_png(f.read())
        except Exception:
            payload = None
        if payload:
            payload["file"] = fn
            payload["slug"] = fn[:-4]
            payload["source"] = "github" if full and not full.startswith("local/") else "local"
            payload["sourceKey"] = full if payload["source"] == "github" else None
            payload["locallyEdited"] = bool((rec or {}).get("locally_edited"))
            if not payload.get("requirements"):
                payload["requirements"] = list((rec or {}).get("requirements") or [])
            chips.append(payload)
        else:
            # Build .86 (issue #79): a cartridge that fails to
            # parse is never silently dropped — it surfaces as an
            # unreadable entry (filename for a name, empty code)
            # so the Local tab can show it honestly, still
            # deletable, instead of the chip simply vanishing.
            chips.append({
                "name": fn[:-4],
                "description": "",
                "code": "",
                "output": "",
                "files": [],
                "file": fn,
                "slug": fn[:-4],
                "source": "github" if full and not full.startswith("local/") else "local",
                "sourceKey": full if full and not full.startswith("local/") else None,
                "locallyEdited": bool((rec or {}).get("locally_edited")),
                "unreadable": True,
                "requirements": list((rec or {}).get("requirements") or []),
            })
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


def _chip_keys(chip):
    return {
        chip["slug"].lower(),
        chip["name"].lower(),
        re.sub(r"[^a-z0-9]+", "-", chip["name"].lower()).strip("-"),
    }


def resolve_chip_invocation(rest, chips):
    # The ./ resolver (0.1.9e, issue #97): "./name args..." with the
    # name resolved in widening rings — the exact slug or name, then
    # the name with a leading "navi-" forgiven on either side
    # ("./cryptex" finds navi-cryptex), then a unique prefix. Returns
    # (chip, args) on a run, (None, candidates) when more than one
    # chip fits, and (None, []) when nothing does.
    text = (rest or "").strip()
    if not text:
        return None, []
    parts = text.split(None, 1)
    token = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    for chip in chips:
        if token in _chip_keys(chip):
            return chip, args
    bare = token[5:] if token.startswith("navi-") else token
    for chip in chips:
        keys = {k[5:] if k.startswith("navi-") else k for k in _chip_keys(chip)}
        if bare in keys:
            return chip, args
    hits = []
    for chip in chips:
        keys = set(_chip_keys(chip)) | {
            k[5:] if k.startswith("navi-") else k for k in _chip_keys(chip)
        }
        if any(k.startswith(token) or k.startswith(bare) for k in keys if k):
            hits.append(chip)
    if len(hits) == 1:
        return hits[0], args
    return None, hits


def chip_shelf_reply(inv):
    # The shelf as a chat reply: every chip on this machine with its
    # one-line description, for a bare "/chip" or a bare "./".
    shelf = local_chips()
    if not shelf:
        return (
            "No chips are installed yet — the shelf is empty. Open the Chips tab and "
            "install one from the GitHub catalog (Navi User Repo) or forge your own in Chip "
            "Studio; then it lands here and " + inv + " <name> runs it."
        )
    lines = []
    for c in shelf:
        d = (c.get("description") or "").strip()
        if len(d) > 90:
            d = d[:87] + "..."
        lines.append("• " + c["name"] + (" — " + d if d else ""))
    return (
        "On the shelf — " + inv + " <name> runs one:\n"
        + "\n".join(lines)
    )


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

# The navi.py compatibility shim (build .86, issue #79): chips
# written for the original Navi import navi and call
# get_parameters(text). The shim rides the same stub navi_internal
# uses and restores the old semantics exactly: get_parameters
# returns the shlex-split token list with the command name
# INCLUDED — the chip's run() pops it, the way the old chips were
# written. Written beside every sandbox unless the chip ships its
# own navi.py.
NAVI_PY_SHIM = '''
import shlex
from navi_internal import navi_instance, NaviApp

def get_parameters(text):
    try:
        return shlex.split(text or "")
    except Exception:
        return (text or "").split()
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
        # The navi.py compatibility shim (build .86, issue #79)
        # rides EVERY sandbox — unless the chip ships its own
        # navi.py, which always wins.
        chip_files_pre = chip.get("files") or []
        if not any(isinstance(it, dict) and str(it.get("path") or "") == "navi.py" for it in chip_files_pre):
            with open(os.path.join(tmp, "navi.py"), "w") as f:
                f.write(NAVI_PY_SHIM)
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
        # Package mode (build .86, issue #79): when the entry
        # code uses relative imports, or the file set carries
        # package directories, the entry loads as a package
        # member — it is written into a synthetic package with
        # the chip's package folders beside it, and the runner
        # imports it as chip_pkg.chip_entry, so a relative
        # import (from .app_cryptex...) resolves, and a plain
        # "import app_cryptex..." finds the package too — the
        # package dir itself joins the path.
        file_paths = [str(it.get("path") or "") for it in chip_files if isinstance(it, dict)]
        package_mode = (
            re.search(r"^\s*from\s+\." , code, re.M) is not None
            or any("/" in p for p in file_paths)
        )
        if package_mode:
            pkg_dir = os.path.join(tmp, "chip_pkg")
            os.makedirs(pkg_dir, exist_ok=True)
            with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
                f.write("")
            with open(os.path.join(pkg_dir, "chip_entry.py"), "w") as f:
                f.write(code)
            for item in chip_files:
                if not isinstance(item, dict):
                    continue
                rel = str(item.get("path") or "")
                if "/" not in rel or rel.startswith("/") or ".." in rel.split("/"):
                    continue
                dest = os.path.join(pkg_dir, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w") as f:
                    f.write(str(item.get("content") or ""))
            runner = (
                "import sys, types\n"
                "sys.path.insert(0, sys.argv[1])\n"
                "sys.path.insert(0, sys.argv[1] + \"/chip_pkg\")\n"
                "import chip_pkg.chip_entry as chip_module\n"
                "args = types.SimpleNamespace(text=sys.argv[2])\n"
                "chip_module.run(args)\n"
            )
        else:
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
        "Edit the documents, bump `version` in `navi-rag.json`, push, and publish",
        "a new release — the version tag is created with that publish (this export is `"
        + version + "`). A newer release is what offers everyone who",
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


def rag_readme_override(slug):
    # The operator's edited README for a pack, kept in the pack
    # folder as a hidden file (no .md/.txt suffix, so it is never
    # collected as a document). None when they have not edited it —
    # the generated README ships instead.
    try:
        with open(os.path.join(RAG_PACKS_DIR, slug, ".readme-override")) as f:
            return f.read()
    except Exception:
        return None


def rag_repo_files(slug, version):
    # The pack's GitHub-ready repo file set — the exact files the
    # export ZIP holds and the publish upload sends, README override
    # included when the operator edited one.
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
    override = rag_readme_override(slug)
    if override is not None:
        files = [(arc, override if arc == "README.md" else data) for arc, data in files]
    return files


def export_rag_pack(slug, version):
    # Builds the pack's GitHub-ready repo ZIP in rag-exports/ and
    # returns (zip file name, [repo file names]).
    files = rag_repo_files(slug, version)
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
    # Issue #99: the export's version rides inside the forged
    # picture too, so the artifact states its own version wherever
    # it travels — the export's manifest and its picture agree.
    chip = dict(chip)
    chip["version"] = version
    manifest = {
        "format": "navi-chip/1",
        "name": chip["name"],
        "description": chip.get("description") or "",
        "version": version,
        "entry": "root.py",
        "files": [f["path"] for f in chip_files],
        "output": chip.get("output") or "",
        "glyph": pick_chip_glyph(chip) or "",
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
        "Edit the code, bump `version` in `navi-chip.json`, and press",
        "**Publish to GitHub** on the chip's card in Apex — Publish does",
        "everything: repo, files, topic, the version tag, and the published",
        "release with this picture attached (this export is `"
        + version + "`). Publishing by hand from an export ZIP works too —",
        "push the files and publish a release; the version tag is created",
        "with that publish. A newer release is what offers everyone who",
        "installed the chip an update. Keep the `navi-chips` topic on the",
        "repo — that is how Navi finds it.",
        "",
    ]
    gitignore = chr(10).join([".DS_Store", "Thumbs.db", "__pycache__/", ""])
    # An operator-edited README (kept inside the cartridge as
    # "readme") ships instead of the generated page, in the export
    # ZIP and the publish upload alike.
    readme_text = chip.get("readme") or chr(10).join(lines)
    files = [
        ("README.md", readme_text),
        ("navi-chip.json", json.dumps(manifest, indent=2) + chr(10)),
    ]
    for f in chip_files:
        files.append((f["path"], f["content"]))
    files.append((slug + ".png", build_cartridge_png(chip)))
    files.append((".gitignore", gitignore))
    return files


def load_local_chip(fname):
    path = os.path.join(CHIPS_DIR, os.path.basename(fname or ""))
    if not fname.endswith(".png") or not os.path.isfile(path):
        raise ValueError("That chip is not in the chips folder.")
    with open(path, "rb") as f:
        chip = parse_cartridge_png(f.read())
    if not chip:
        raise ValueError("That chip could not be read.")
    chip["file"] = os.path.basename(fname)
    return chip


def save_local_chip_readme(fname, readme):
    # Persists (or clears, when readme is None) the operator's
    # edited README inside the chip cartridge itself, so it travels
    # with the chip and survives re-export and re-publish.
    chip = load_local_chip(fname)
    if readme is None:
        chip.pop("readme", None)
    else:
        chip["readme"] = readme
    path = os.path.join(CHIPS_DIR, os.path.basename(fname))
    with open(path, "wb") as f:
        f.write(build_cartridge_png(chip))


def export_chip(fname, version):
    # Builds a local chip's GitHub-ready repo ZIP in
    # chips-exports/ and returns (zip file name, [repo file names]).
    chip = load_local_chip(fname)
    files = build_chip_repo_files(chip, version)
    os.makedirs(CHIPS_EXPORTS_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", chip["name"].lower()).strip("-") or "chip"
    safe_version = re.sub(r"[^0-9A-Za-z.-]+", "-", version).strip("-.") or "0.1.0"
    zip_name = slug + "-" + safe_version + ".zip"
    with zipfile.ZipFile(os.path.join(CHIPS_EXPORTS_DIR, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        for arc, data in files:
            z.writestr(arc, data)
    return zip_name, [arc for arc, _data in files]


def github_publish_files(repo_name, files, topic, description, release=None):
    # The publish loop, shared by RAG packs and chips — the WHOLE
    # chain in one action (0.1.9e): create the repo on the signed-in
    # account when it is not there (public — the catalogs only find
    # public repos), apply the topic with no prompt, upload the
    # exact file set the export builds, then create the tag and
    # PUBLISH the release (never a draft), named from the manifest
    # version, with the cartridge picture attached as the release
    # asset. The retired never-releases line is gone: Publish
    # does everything — repo, files, topic, tag, release, picture
    # attached. `release` carries {version, title, notes, assetName,
    # assetData}; when it is None the loop stops after the upload,
    # as before. A tag that already has a release is refused BEFORE
    # anything uploads — a release is never overwritten silently.
    # Returns a result dict; failures carry the real reason and
    # never fake a success (a failure after the upload says plainly
    # that the files landed and the release did not).
    auth = github_auth()
    if not auth:
        return {"ok": False, "error": "You are not signed in to GitHub. Sign in under Settings → GitHub & Backup, or use Export for GitHub and upload the ZIP yourself."}
    login, token = auth["login"], auth["token"]
    # Every call below goes through pub(): it carries the current
    # token, and on a 401 it renews the sign-in once from the
    # stored refresh token and retries the call once (issue #14).
    # A 401 that survives that — or arrives with no refresh token
    # stored — means the saved sign-in is dead, and the operator
    # hears that in plain words, never as a raw HTTP string.
    state = {"token": token, "renewed": False}

    def reauth_error():
        return {"ok": False, "error": "GitHub rejected the sign-in Navi has saved — the token has expired or been revoked, and Navi could not renew it. Sign out and back in under Settings → GitHub & Backup, then publish again. Nothing was uploaded."}

    def pub(method, url, body=None):
        st, resp = github_api(method, url, state["token"], body)
        if st == 401 and not state["renewed"]:
            state["renewed"] = True
            fresh = github_refresh_auth()
            if fresh:
                state["token"] = fresh["token"]
                st, resp = github_api(method, url, state["token"], body)
        return st, resp

    def pub_raw(method, url, data, content_type):
        st, resp = github_api_raw(method, url, state["token"], data, content_type)
        if st == 401 and not state["renewed"]:
            state["renewed"] = True
            fresh = github_refresh_auth()
            if fresh:
                state["token"] = fresh["token"]
                st, resp = github_api_raw(method, url, state["token"], data, content_type)
        return st, resp

    name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(repo_name or "")).strip("-.")[:100]
    if not name:
        return {"ok": False, "error": "The repo name came out empty — give it a name before publishing."}
    if not login:
        st, me = pub("GET", "https://api.github.com/user")
        if st == 401:
            return reauth_error()
        if st == 200 and isinstance(me, dict):
            login = str(me.get("login") or "")
    if not login:
        return {"ok": False, "error": "GitHub did not say whose account this is — sign out and back in under Settings → GitHub & Backup, then try again."}
    base = "https://api.github.com/repos/" + login + "/" + name
    st, _repo = pub("GET", base)
    created = False
    if st == 401:
        return reauth_error()
    if st == 404:
        st2, resp = pub("POST", "https://api.github.com/user/repos", {
            "name": name, "description": description or "", "private": False,
        })
        if st2 == 401:
            return reauth_error()
        if st2 not in (200, 201):
            return {"ok": False, "error": "GitHub would not create the repo (HTTP " + str(st2) + "): " + github_err_text(resp) + " If the sign-in token cannot create repos, make a public repo named " + name + " on GitHub yourself and publish again — Navi will upload into it — or use Export for GitHub."}
        created = True
    elif st != 200:
        return {"ok": False, "error": "GitHub would not answer for that repo (HTTP " + str(st) + "): " + github_err_text(_repo)}
    # Release pre-check: a version that already has a release is
    # refused before a single file uploads — bump the version in
    # the manifest instead. (A leftover tag with NO release does
    # not block: creating the release below adopts it.)
    rel_tag = None
    if release and release.get("version"):
        rel_tag = "v" + str(release["version"]).strip().lstrip("v")
        stg, rel_existing = pub("GET", base + "/releases/tags/" + urllib.parse.quote(rel_tag))
        if stg == 401:
            return reauth_error()
        if stg == 200 and isinstance(rel_existing, dict):
            return {"ok": False, "error": rel_tag + " is already released on " + login + "/" + name + " — bump the version in the manifest and publish again. Nothing was uploaded and the existing release was not touched."}
    # Topic: merge with whatever is already there, never prompt.
    _st3, topics_resp = pub("GET", base + "/topics")
    if _st3 == 401:
        return reauth_error()
    names = topics_resp.get("names") if isinstance(topics_resp, dict) else []
    merged = sorted(set(list(names or []) + [topic]))
    _stt, _tresp = pub("PUT", base + "/topics", {"names": merged})
    if _stt == 401:
        return reauth_error()
    # Upload each file through the contents API (sha when updating).
    for arc, data in files:
        raw = data if isinstance(data, bytes) else str(data).encode("utf-8")
        body = {
            "message": ("Publish " if created else "Update ") + arc,
            "content": base64.b64encode(raw).decode("ascii"),
        }
        url = base + "/contents/" + urllib.parse.quote(arc)
        stx, existing = pub("GET", url)
        if stx == 401:
            return reauth_error()
        if stx == 200 and isinstance(existing, dict) and existing.get("sha"):
            body["sha"] = existing["sha"]
        st4, resp4 = pub("PUT", url, body)
        if st4 == 401:
            return reauth_error()
        if st4 not in (200, 201):
            return {"ok": False, "error": "Uploading " + arc + " failed (HTTP " + str(st4) + "): " + github_err_text(resp4)}
    result = {
        "ok": True, "error": None, "created": created,
        "repo": login + "/" + name,
        "repoUrl": "https://github.com/" + login + "/" + name,
        "files": [arc for arc, _d in files],
    }
    if rel_tag:
        notes = str(release.get("notes") or "")
        if len(notes) > 120000:
            notes = notes[:120000]
        st5, rel = pub("POST", base + "/releases", {
            "tag_name": rel_tag,
            "name": str(release.get("title") or rel_tag),
            "body": notes,
            "draft": False,
            "prerelease": False,
        })
        if st5 == 401:
            return {"ok": False, "error": "The files are uploaded to " + login + "/" + name + ", but GitHub rejected the sign-in when the release step ran and Navi could not renew it. Sign out and back in under Settings \u2192 GitHub & Backup, then publish again — the files are already there."}
        if st5 not in (200, 201) or not isinstance(rel, dict):
            return {"ok": False, "error": "The repo, topic, and files are on GitHub (" + login + "/" + name + "), but GitHub would not create the release (HTTP " + str(st5) + "): " + github_err_text(rel) + " If the sign-in token cannot create releases, publish the " + rel_tag + " release on GitHub yourself — the files and the picture are already uploaded."}
        rel_info = {
            "tag": rel_tag,
            "url": rel.get("html_url") or ("https://github.com/" + login + "/" + name + "/releases/tag/" + rel_tag),
            "asset": None,
        }
        asset_name = str(release.get("assetName") or "")
        asset_data = release.get("assetData")
        if asset_name and isinstance(asset_data, (bytes, bytearray)) and rel.get("id"):
            up_url = ("https://uploads.github.com/repos/" + login + "/" + name
                      + "/releases/" + str(rel["id"]) + "/assets?name="
                      + urllib.parse.quote(asset_name))
            st6, _asset = pub_raw("POST", up_url, bytes(asset_data), "application/octet-stream")
            if st6 == 401:
                return {"ok": False, "error": "The release " + rel_tag + " is published on " + login + "/" + name + ", but GitHub rejected the sign-in when the picture attach ran. Attach " + asset_name + " to the release on GitHub — it is already at the repo root too."}
            if st6 not in (200, 201):
                return {"ok": False, "error": "The release " + rel_tag + " is published on " + login + "/" + name + ", but attaching the picture failed (HTTP " + str(st6) + "): " + github_err_text(_asset) + " The picture is at the repo root; attach " + asset_name + " to the release on GitHub if you want it there too."}
            rel_info["asset"] = asset_name
        result["release"] = rel_info
    return result


def _rag_pack_index(slug):
    try:
        with open(os.path.join(RAG_PACKS_DIR, slug, "index.json")) as f:
            index = json.load(f)
        return index if isinstance(index, dict) else None
    except Exception:
        return None


# --- Knowledge cartridges (0.1.9e, issue #93) -----------------------
# A RAG pack can ride a picture the way a chip does: one PNG whose
# "navi-rag" tEXt chunk carries the pack's manifest and ALL of its
# document texts, zlib-compressed and base64'd. Installing from the
# picture validates it like a repo install and writes the pack with
# write_rag_pack — which builds the search index LOCALLY, at install
# time, from the carried texts. A cartridge never carries an index,
# and nothing at query time ever reads the picture: once installed,
# a pack is a pack. The ceiling is the finished picture's size: past
# it the answer is an honest refusal, never a silent truncation.
RAG_CARTRIDGE_MAX_BYTES = 8 * 1024 * 1024


def build_rag_cartridge_png(payload):
    # Build 2: the knowledge cartridge wears the same card-grade
    # face as a chip — the face builder reads the pack's own name,
    # description, version, and document count off the payload.
    face = _cartridge_face_png(payload, "navi-rag")
    blob = base64.b64encode(
        zlib.compress(json.dumps(payload).encode("utf-8"), 9)
    )
    text = b"navi-rag\x00" + blob
    ihdr_end = 8 + 12 + 13
    return face[:ihdr_end] + _png_chunk(b"tEXt", text) + face[ihdr_end:]


def parse_rag_cartridge_png(data):
    # (payload, error): the inverse of build_rag_cartridge_png,
    # with the Mesh card import's honesty rules — a picture with no
    # payload, a damaged one, and the wrong kind of picture each get
    # their own words.
    if not isinstance(data, (bytes, bytearray)) or len(data) < 8 or bytes(data[:8]) != b"\x89PNG\r\n\x1a\n":
        return None, "That file is not a PNG image — a knowledge cartridge travels as a .png picture."
    data = bytes(data)
    pos = 8
    blob = None
    saw_other = False
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            return None, "This picture started life as a knowledge cartridge, but the data inside it is damaged — it no longer reads whole, so nothing was installed."
        chunk_data = data[pos + 8:pos + 8 + length]
        if kind == b"tEXt":
            nul = chunk_data.find(b"\x00")
            if nul > 0:
                if chunk_data[:nul] == b"navi-rag":
                    (crc_stored,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
                    if binascii.crc32(kind + chunk_data) & 0xFFFFFFFF != crc_stored:
                        return None, "This picture started life as a knowledge cartridge, but the data inside it is damaged — it no longer reads whole, so nothing was installed."
                    blob = chunk_data[nul + 1:]
                else:
                    saw_other = True
        if kind == b"IEND":
            break
        pos += 8 + length + 4
    if blob is None:
        if saw_other:
            return None, "That picture carries a different kind of payload — it is not a knowledge cartridge. Knowledge cartridges are exported from RAG Studio."
        return None, "This image has no readable knowledge-cartridge data — it may have been recompressed by a chat app, which strips the data out of the picture while leaving the picture itself looking fine. Send the original file inside a .zip instead."
    try:
        payload = json.loads(zlib.decompress(base64.b64decode(blob)).decode("utf-8"))
    except Exception:
        return None, "This picture started life as a knowledge cartridge, but the data inside it is damaged — it no longer reads whole, so nothing was installed."
    if not isinstance(payload, dict) or payload.get("format") != "navi-rag/1":
        return None, "That picture's cartridge data is not in the shape a knowledge cartridge carries — nothing was installed."
    return payload, ""


def rag_cartridge_payload(slug):
    # The cartridge payload for an installed pack: its manifest and
    # every document's full text, read back from the pack folder.
    src = rag_pack_documents(slug)
    if src is None:
        return None
    index = _rag_pack_index(slug) or {}
    return {
        "format": "navi-rag/1",
        "name": src["name"],
        "description": src["description"],
        "version": "0.1.0",
        "documents": src["documents"],
        "generatedBy": "Apex — RAG Studio cartridge export",
        "chunkCountAtExport": index.get("chunkCount") or 0,
    }


def install_rag_cartridge(payload):
    # The one cartridge install path (Deck drops and the RAG tab's
    # picture install both land here). Validation mirrors a repo
    # install's caps; the pack is written by write_rag_pack, so its
    # index is built on this machine from the carried texts.
    name = str(payload.get("name") or "").strip()[:120]
    description = str(payload.get("description") or "")[:500]
    documents = []
    for raw in payload.get("documents") or []:
        if not isinstance(raw, dict):
            continue
        body = str(raw.get("body") or "")
        if not body.strip():
            continue
        if len(body) > RAG_MAX_DOC_CHARS:
            return None, "One document in this cartridge is longer than a pack document may be (" + str(RAG_MAX_DOC_CHARS) + " characters) — nothing was installed."
        documents.append({"title": str(raw.get("title") or "document")[:200], "body": body})
    if not name:
        return None, "This cartridge's pack has no name — nothing was installed."
    if not documents:
        return None, "This cartridge carries no documents — nothing was installed."
    if len(documents) > RAG_MAX_DOCS:
        return None, "This cartridge carries " + str(len(documents)) + " documents — a pack caps at " + str(RAG_MAX_DOCS) + ". Nothing was installed."
    rows = load_rag_installs()
    slug = chip_slug(name)
    taken = {r.get("local_dir") for r in rows if r.get("full_name") != "local/" + slug}
    taken |= {
        e for e in os.listdir(RAG_PACKS_DIR)
        if os.path.isdir(os.path.join(RAG_PACKS_DIR, e))
    } if os.path.isdir(RAG_PACKS_DIR) else set()
    if slug in taken or any(r.get("full_name") == "local/" + slug for r in rows):
        return None, "A pack named " + name + " is already on this machine — remove it first, or rename the cartridge's pack."
    write_rag_pack(slug, name, description, documents)
    rows.append({
        "full_name": "local/" + slug,
        "name": name,
        "html_url": "",
        "installed_tag": None,
        "installed_ref": "knowledge cartridge (.png)",
        "installed_pushed_at": None,
        "installed_at": _now_iso(),
        "local_dir": slug,
        "active": True,
        "doc_count": len(documents),
    })
    save_rag_installs(rows)
    return slug, ""


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
            "installedRef": _display_ref(rec.get("installed_ref")) if rec else None,
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


# ------------------------------- The Vault -------------------------------
# Build .72, issue #54: a shared desk of plain markdown notes at
# config/vault/ inside the install — real .md files in subfolders,
# YAML frontmatter preserved, [[wikilinks]] and #tags as plain text,
# so the operator can open the same folder in Obsidian and
# everything works. Every path is jailed to the vault root; writes
# land atomically (temp file + rename); the seed runs only when the
# folder does not exist yet and never touches an existing file.

VAULT_DIR = os.path.join(ROOT, "config", "vault")


def _vault_seed_files():
    today = time.strftime("%Y-%m-%d", time.localtime())
    welcome = "\n".join([
        "---", "tags: [vault, guide]", "---", "",
        "# Welcome to the Vault", "",
        "This folder is a shared desk: plain markdown files you can open here, in Obsidian, or in any text editor — same files, no conversion, nothing locked in.", "",
        "## The two areas", "",
        "- **Navi's Desk/** — her side of the desk. When a conversation produces something worth keeping — a decision, a finding, something you asked her to remember — she files a dated note here and tells you she did.",
        "- **Operator/** — your side. She never edits your notes silently: she writes here only when you ask her to in chat, and she says what she filed.",
        "- **Daily/** — one note per day, from the Daily Note button.",
        "- **Templates/** — files here are offered as starting templates when you make a new note.", "",
        "## Conventions", "",
        "- Link notes with [[wikilinks]] — click one in Preview to jump (or to create the note).",
        "- Tag with #tags anywhere in the text.",
        "- YAML frontmatter at the top of a note stays exactly as written; the preview never mangles it.", "",
        "The vault folder rides the installer's keep-list, so updates and fresh installs preserve it. See [[Start here]] on your side of the desk, and [[First note]] on hers.", "",
    ])
    first = "\n".join([
        "---", "filed: " + today, "---", "",
        "# First note", "",
        "Filed " + today + " — my first note on my side of the desk.", "",
        "This is where I'll keep what a conversation produces that's worth more than the conversation: decisions we made and why, findings from the work, things you asked me to remember. Dated, first person, in my own words — and when one of these notes informs an answer I give you, I'll name it as a source, the way I name a RAG pack.", "",
        "Your notes live in [[Start here]]'s folder, and I won't touch them unless you ask. The desk is shared; the sides are respected.", "",
        "#navi #desk", "",
    ])
    start = "\n".join([
        "# Start here", "",
        "Your side of the desk. Make a note with **New note**, drag notes between folders in the tree, or drop markdown files from your computer onto the vault to import them.", "",
        "Ask Navi in chat to file something here and she will — out loud, never silently. Her own notes live across the desk in [[First note]].", "",
    ])
    template = "\n".join([
        "---", "tags: []", "---", "",
        "# Untitled", "",
        "## Notes", "", "- ", "",
        "## Links", "", "- [[Welcome]]", "",
    ])
    return [
        ("Welcome.md", welcome),
        ("Navi's Desk/First note.md", first),
        ("Operator/Start here.md", start),
        ("Templates/Note template.md", template),
    ]


def vault_join(rel):
    # The jail: normalize a vault-relative path, or return None for
    # anything that escapes the vault root (.., absolute, empty).
    rel = str(rel or "").replace(chr(92), "/").strip()
    if not rel or rel.startswith("/"):
        return None
    parts = []
    for seg in rel.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            return None
        parts.append(seg)
    if not parts:
        return None
    root = os.path.abspath(VAULT_DIR)
    full = os.path.abspath(os.path.join(root, *parts))
    if full != root and not full.startswith(root + os.sep):
        return None
    return "/".join(parts)


def vault_fs_path(rel):
    return os.path.join(VAULT_DIR, *rel.split("/"))


def vault_write(rel, content):
    full = vault_fs_path(rel)
    parent = os.path.dirname(full)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = full + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(str(content))
    os.replace(tmp, full)


def vault_ensure_seed():
    # First run only: if the folder already exists, the operator's
    # desk is theirs — seeding never writes into it again.
    if os.path.isdir(VAULT_DIR):
        return
    os.makedirs(VAULT_DIR, exist_ok=True)
    for rel, content in _vault_seed_files():
        if not os.path.exists(vault_fs_path(rel)):
            vault_write(rel, content)


def _vault_links(content):
    out = []
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content or ""):
        t = m.group(1).strip()
        if t and t not in out:
            out.append(t)
    return out


def _vault_tags(content):
    out = []
    for m in re.finditer(r"(?m)(?:^|\s)#([A-Za-z][A-Za-z0-9_-]*)", content or ""):
        t = m.group(1)
        if t and t not in out:
            out.append(t)
    return out


def vault_notes_raw():
    vault_ensure_seed()
    notes = []
    if os.path.isdir(VAULT_DIR):
        for base, dirs, files in os.walk(VAULT_DIR):
            dirs.sort()
            for name in sorted(files):
                if not name.lower().endswith(".md"):
                    continue
                full = os.path.join(base, name)
                rel = os.path.relpath(full, VAULT_DIR).replace(os.sep, "/")
                try:
                    with open(full, encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue
                notes.append({
                    "path": rel,
                    "content": content,
                    "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(full))),
                })
    notes.sort(key=lambda n: n["path"])
    return notes


def vault_list_payload():
    notes = vault_notes_raw()
    folders = set()
    if os.path.isdir(VAULT_DIR):
        for base, dirs, files in os.walk(VAULT_DIR):
            for d in dirs:
                rel = os.path.relpath(os.path.join(base, d), VAULT_DIR).replace(os.sep, "/")
                folders.add(rel)
    for n in notes:
        parts = n["path"].split("/")
        title = parts[-1][:-3] if parts[-1].lower().endswith(".md") else parts[-1]
        n["title"] = title
        n["outgoing"] = _vault_links(n["content"])
        n["tags"] = _vault_tags(n["content"])
    for n in notes:
        n["backlinks"] = [
            o["path"] for o in notes
            if o["path"] != n["path"]
            and any(t.lower() == n["title"].lower() for t in o["outgoing"])
        ]
    return {"notes": notes, "folders": sorted(folders)}


def vault_search(query, limit=2):
    words = set(w for w in re.findall(r"[a-z0-9][a-z0-9_-]{3,}", (query or "").lower()))
    if not words:
        return []
    scored = []
    for n in vault_notes_raw():
        title = n["path"].split("/")[-1].lower()
        tags = [t.lower() for t in _vault_tags(n["content"])]
        body = n["content"].lower()
        score = 0
        for w in words:
            if w in title:
                score += 3
            if w in tags:
                score += 2
            if w in body:
                score += 1
        if score > 0:
            prose = re.sub(r"^---\n.*?\n---\n", "", n["content"], flags=re.S)
            lines = [ln.strip() for ln in prose.split("\n") if ln.strip() and not ln.strip().startswith("#")]
            scored.append({"path": n["path"], "score": score, "excerpt": " ".join(lines)[:400]})
    scored.sort(key=lambda h: -h["score"])
    return scored[:limit]


def vault_file_from_chat(text, history=None):
    # Her note-taking from chat (issue #54): a filing request lands
    # on her side of the desk — Navi's Desk/, dated, first person —
    # unless the operator names their own side. The note is ABOUT
    # something: the thing just discussed. A bare request ("make a
    # note about that up there") names no subject, so the recent
    # conversation rides along (build .73, field report: the first
    # version filed an empty note under a promising name): the note
    # says what it is about and quotes the exchange it came from —
    # above all the latest terminal output. Returns (path, err).
    raw = (text or "").strip()
    to_operator = bool(re.search(r"\b(?:in|to|under)\s+(?:my|the\s+operator|operator)\b", raw, re.I))
    body = raw.split(":", 1)[1].strip() if ":" in raw else raw
    body = re.sub(r"^(?:please\s+)?(?:file|write|save|make|take)\s+(?:a\s+|this\s+)?note\b", "", body, flags=re.I).strip()
    body = re.sub(r"\bnote\s+(?:this|that)\s+down\b", "", body, flags=re.I).strip() or raw
    # The subject as the operator phrased it, with the politeness and
    # the filing verbs stripped: "Can you make a note about X" -> "X".
    subject = body
    subject = re.sub(r"^(?:please\s+)?(?:can|could|would)\s+you\s+", "", subject, flags=re.I).strip()
    subject = re.sub(r"^(?:please\s+)?(?:file|write|save|make|take)\s+(?:a\s+|this\s+)?note\s+(?:about|on|of)\s+", "", subject, flags=re.I).strip()
    subject = re.sub(r"^(?:please\s+)?(?:file|write|save|make|take)\s+(?:a\s+|this\s+)?note\b\s*", "", subject, flags=re.I).strip(" .?:")
    # Recent conversation, newest first, skipping the request itself.
    ctx = []
    for item in reversed(history or []):
        if not isinstance(item, dict):
            continue
        c = str(item.get("content") or "").strip()
        if not c or c == raw:
            continue
        ctx.append(c)
        if len(ctx) >= 3:
            break
    term = ""
    for c in ctx:
        if "terminal" in c.lower() or c.startswith("$ "):
            term = c
            break
    term_cmd = ""
    if term:
        for ln in term.split("\n"):
            ln = ln.strip()
            if ln.startswith("$ "):
                term_cmd = ln[2:].strip()
                break
    vague = (not subject) or len(subject.split()) < 2 or bool(re.match(r"(?i)^(that|this|it|the above|up there)\b", subject))
    # Her titles name the SUBJECT, never the operator's ask (field
    # report: a filing named "Can you make a note" after his literal
    # words). A vague ask over a terminal result titles the note for
    # what the terminal showed — for a listing, the place listed and
    # the first thing in it.
    if not vague:
        title_src = subject
    elif term_cmd:
        title_src = ""
        m_ls = re.match(r"ls\s+(?:-\S+\s+)*(\S+)", term_cmd)
        if m_ls:
            seg = m_ls.group(1).rstrip("/").split("/")[-1] or "root"
            first_entry = ""
            seen_cmd = False
            for ln in term.split("\n"):
                s_ln = ln.strip()
                if s_ln.startswith("$ "):
                    seen_cmd = True
                    continue
                if seen_cmd and s_ln:
                    tok = s_ln.split()[0]
                    if not tok.endswith(":"):
                        first_entry = tok
                        break
            title_src = seg + " listing - " + first_entry if first_entry else seg + " listing"
        if not title_src:
            title_src = "Terminal - " + term_cmd
    elif ctx:
        title_src = ctx[-1]
    else:
        title_src = subject or body
    if len(title_src) > 80:
        title_src = " ".join(title_src.split()[:6])
    title = " ".join(title_src.replace("#", "").split()).strip(" .:") or "Untitled note"
    title = title.replace("/", "-").replace(chr(92), "-")
    today = time.strftime("%Y-%m-%d", time.localtime())
    folder = "Operator" if to_operator else "Navi's Desk"
    rel = folder + "/" + today + " " + title + ".md"
    n = 2
    while os.path.exists(vault_fs_path(rel)):
        rel = folder + "/" + today + " " + title + " " + str(n) + ".md"
        n += 1
    if to_operator:
        content = "# " + title + "\n\n" + body + "\n"
    else:
        lines = [
            "---", "filed: " + today, "---", "",
            "# " + title, "",
            "Alex asked me to keep a note of this, " + today + " — in his words: “" + raw + "”", "",
            "## What it's about", "",
        ]
        if not vague:
            lines += [subject[0].upper() + subject[1:] if subject else subject, ""]
        elif term_cmd:
            lines += ["The terminal output from just before he asked — the “" + term_cmd + "” run, kept below so the note stands on its own.", ""]
        elif ctx:
            lines += ["The exchange just before he asked, kept below so the note stands on its own.", ""]
        else:
            lines += ["He asked with nothing else on the table — the request itself is the record, and this line is me saying so instead of filing an empty page.", ""]
        if ctx:
            lines += ["## From the conversation", ""]
            for c in reversed(ctx):
                excerpt = c if len(c) <= 900 else c[:900] + "\n... [trimmed]"
                for ln in excerpt.split("\n"):
                    lines.append("    " + ln)
                lines.append("")
        lines += ["— filed by Navi from chat, " + today + ".", ""]
        content = "\n".join(lines)
    vault_write(rel, content)
    return rel, None


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
    # Issue #22, the pack half — the case from Alex's screenshot:
    # a pack forged in RAG Studio (its local/ record, folder named
    # for the pack) must read as installed on its repo's catalog
    # card, not NOT INSTALLED with a live Install above the local
    # card proving otherwise. Same slug rule as chips: the repo
    # name is matched against the pack folders on this machine
    # and the install records, local/ ones included. An exact
    # full-name match keeps the update math; a slug match claims
    # only "installed" and borrows its state from the local pack.
    installs_ci = {}
    rec_by_slug = {}
    for row in load_rag_installs():
        fn = row.get("full_name") or ""
        if fn:
            installs_ci.setdefault(fn.lower(), row)
        s = fn.split("/")[-1].lower()
        if s and s not in rec_by_slug:
            rec_by_slug[s] = row
    local_packs = {}
    for lp in local_rag_packs():
        local_packs.setdefault(str(lp.get("slug") or "").lower(), lp)
    packs = []
    for repo in repos:
        inst = installs.get(repo["fullName"]) or installs_ci.get(repo["fullName"].lower())
        slug_lp = None
        slug_rec = None
        if not inst:
            s = repo["fullName"].split("/")[-1].lower()
            slug_lp = local_packs.get(s)
            slug_rec = rec_by_slug.get(s)
        slug_matched = bool(not inst and (slug_lp is not None or slug_rec is not None))
        update = False
        if inst:
            if repo["latestRelease"]:
                update = inst.get("installed_tag") != repo["latestRelease"]["tag"]
            else:
                update = bool(
                    inst.get("installed_pushed_at")
                    and repo["pushedAt"] > inst["installed_pushed_at"]
                )
        if inst:
            ref = _display_ref(inst.get("installed_ref"))
            local_dir = inst.get("local_dir")
            active = bool(inst.get("active", True))
            doc_count = inst.get("doc_count")
            edited = bool(inst.get("locally_edited"))
            tag = inst.get("installed_tag")
            at = inst.get("installed_at")
        elif slug_matched:
            ref = slug_lp.get("installedRef") if slug_lp else (
                _display_ref(slug_rec.get("installed_ref"))
                if slug_rec and str(slug_rec.get("full_name") or "").startswith("local/")
                else None
            )
            local_dir = slug_lp.get("slug") if slug_lp else (slug_rec.get("local_dir") if slug_rec else None)
            active = slug_lp.get("active") if slug_lp else (bool(slug_rec.get("active", True)) if slug_rec else None)
            doc_count = slug_lp.get("docCount") if slug_lp else (slug_rec.get("doc_count") if slug_rec else None)
            edited = slug_lp.get("locallyEdited") if slug_lp else (bool(slug_rec.get("locally_edited")) if slug_rec else False)
            tag = slug_rec.get("installed_tag") if slug_rec else None
            at = slug_rec.get("installed_at") if slug_rec else None
        else:
            ref = None
            local_dir = None
            active = None
            doc_count = None
            edited = False
            tag = None
            at = None
        entry = dict(repo)
        entry["inCatalog"] = True
        entry["installed"] = bool(inst) or slug_matched
        entry["slugMatched"] = slug_matched
        entry["installedTag"] = tag
        entry["installedRef"] = ref
        entry["installedAt"] = at
        entry["updateAvailable"] = update
        entry["localDir"] = local_dir
        entry["active"] = active
        entry["docCount"] = doc_count
        entry["locallyEdited"] = edited
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
            "inCatalog": False, "installed": True, "slugMatched": False,
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

    def _client_is_loopback(self):
        try:
            host = str(self.client_address[0] or "")
        except Exception:
            return False
        return host == "::1" or host.startswith("127.")

    def _public_gate_blocks(self):
        # The gate exists only while the bridge is actually bound
        # publicly (public mode was ON at launch). Loopback callers
        # are never gated. Everyone else needs the acceptance
        # cookie whose value is a hash of the current access code.
        if ACTIVE_BIND_HOST != "0.0.0.0":
            return False
        if self._client_is_loopback():
            return False
        code = public_settings(load_config())["access_code"]
        if not code:
            return True
        want = PUBLIC_COOKIE + "=" + public_token(code)
        parts = [p.strip() for p in (self.headers.get("Cookie") or "").split(";")]
        return want not in parts

    def do_DELETE(self):
        # The only DELETE on the dashboard surface: removing a
        # paired Mesh peer (spec section 3.1). Behind the same
        # public gate as every other dashboard write.
        if self.path.split("?")[0] == "/api/mesh/peers":
            if self._public_gate_blocks():
                self._send(403, {"error": "access code required"})
                return
            cfg = load_config()
            data = self._body()
            target = str(data.get("nodeId") or "")
            block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
            block = dict(block)
            borrow = block.get("borrow") if isinstance(block.get("borrow"), dict) else {}
            borrow = dict(borrow)
            peers = borrow.get("peers") if isinstance(borrow.get("peers"), list) else []
            borrow["peers"] = [p for p in peers if not (isinstance(p, dict) and str(p.get("nodeId") or "") == target)]
            block["borrow"] = borrow
            cfg["mesh"] = block
            save_config(cfg)
            self._send(200, {"ok": True, "mesh": mesh_status_payload(load_config())})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_GET(self):
        _path = self.path.split("?")[0]
        if _path == "/__gate":
            self._send(200, gate_page_html().encode(), "text/html; charset=utf-8")
            return
        # Build .86: the node-facing Mesh endpoints (/mesh/status,
        # /mesh/borrow) are NOT served on this dashboard surface at
        # all — borrowers dial the dedicated Mesh port (the peer
        # card's port) only. The dashboard-local Mesh routes
        # (/mesh/card, /mesh/lend/stop, /api/mesh/*) stay below,
        # behind the gate, exactly as they were.
        if self._public_gate_blocks():
            if _path.startswith("/api/"):
                self._send(403, {"error": "access code required"})
            else:
                self._send(200, gate_page_html().encode(), "text/html; charset=utf-8")
            return
        # Build 9 (#90): GET /mesh/card and /api/mesh/card — the
        # card as copyable text — are REMOVED. Pairing is the PNG
        # picture only; those paths now fall through to this
        # handler's not-found answer like any retired route. The
        # card DATA still exists (mesh_card builds it), but it
        # leaves this machine only inside the PNG below.
        if _path in ("/mesh/card.png", "/api/mesh/card.png"):
            # This node's pairing card as a picture (Build 7,
            # spec section 13; the ONLY card surface since
            # Build 9, #90): a dashboard-surface read behind the
            # public gate above — the DHD proxy never forwards
            # /mesh/* here — answering the PNG whose face is the
            # card and whose payload is the card.
            _cfg = load_config()
            if not mesh_settings(_cfg)["enabled"]:
                self._send(200, {"ok": False, "error": "Apex Mesh is off on this machine — turn it on from the Mesh page first."})
                return
            _ok, _err = mesh_ensure_identity(_cfg)
            if not _ok:
                self._send(200, {"ok": False, "error": _err})
                return
            _ok, _err = mesh_ensure_cert()
            if not _ok:
                self._send(200, {"ok": False, "error": _err})
                return
            self._send(200, build_mesh_card_png(load_config()), "image/png")
            return
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
        elif self.path.startswith("/api/pathcomplete"):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            prefix = (qs.get("prefix") or [""])[0]
            self._send(200, {"entries": path_complete(prefix)})
        elif self.path == "/api/status":
            cfg = load_config()
            endpoint = cfg.get("live", {}).get("llamafile_endpoint", "")
            alive = llamafile_alive(endpoint)
            self._send(200, {
                "app": "Navi: Apex",
                "version": app_version(cfg),
                "versionStatus": app_version_status(cfg),
                "bridge": BRIDGE_BUILD,
                # Build 4: the running process's own Edge build
                # sequence, beside its stamp — the apply helper's
                # confirmation reads it after a relaunch, because
                # the version number alone cannot tell one build
                # of a version from the next.
                "buildSeq": SHIPPED_BUILD_SEQ,
                "port": BRIDGE_PORT,
                "dir": ROOT,
                "root": ROOT,
                "update": update_bg_payload(),
                "updaterChannel": updater_channel(cfg),
                "updaterChannelExplicit": updater_channel_explicit(cfg),
                "model": "navi",
                "llamafile_endpoint": endpoint,
                "llamafile_reachable": alive,
                "publicServer": public_state_payload(cfg, self._client_is_loopback()),
                "dhd": dhd_state_payload(cfg, self._client_is_loopback()),
                "mesh": mesh_status_payload(cfg, (self.headers.get("X-Apex-Via") or "") == "dhd"),
            })
        elif self.path.startswith("/api/operations/"):
            _op_id = urllib.parse.unquote(self.path.rsplit("/", 1)[-1])
            _op = op_snapshot(_op_id)
            if _op:
                self._send(200, {"ok": True, "operation": _op})
            else:
                self._send(404, {"ok": False, "error": "operation not found"})
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
        elif self.path.split("?")[0] == "/api/rag/readme":
            # The back of a pack flip card: the pack repo's README,
            # fetched raw from GitHub on demand — the pack
            # counterpart of /api/chips/readme, same contract. (The
            # POST /api/rag/readme further down is a different
            # thing: the local pack README editor's read.)
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
        elif self.path == "/api/vault/list":
            # The Vault (build .72, issue #54): every note with its
            # exact text, plus folders, wikilinks, tags, backlinks.
            self._send(200, vault_list_payload())
        elif self.path.split("?")[0] == "/api/vault/search":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            self._send(200, {"hits": vault_search((qs.get("q") or [""])[0], 8)})
        elif self.path == "/api/vault/export":
            # The whole folder as a .zip — unzip it and Obsidian
            # opens the result as a vault, exactly as it lies here.
            vault_ensure_seed()
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                if os.path.isdir(VAULT_DIR):
                    for base, dirs, files in os.walk(VAULT_DIR):
                        dirs.sort()
                        for name in sorted(files):
                            full = os.path.join(base, name)
                            z.write(full, os.path.relpath(full, VAULT_DIR).replace(os.sep, "/"))
            self._send(200, buf.getvalue(), "application/zip")
        elif self.path.split("?")[0] == "/api/rag/cartridge.png":
            # The pack as a picture, built on demand from the pack
            # folder (issue #93): the sleeve image the RAG tab and
            # ChipDeck show, and the file a download saves.
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            slug = os.path.basename((qs.get("slug") or [""])[0])
            payload = rag_cartridge_payload(slug) if slug else None
            if payload is None:
                self._send(404, {"error": "not found"})
            else:
                png = build_rag_cartridge_png(payload)
                if len(png) > RAG_CARTRIDGE_MAX_BYTES:
                    self._send(404, {"error": "too big for a picture"})
                else:
                    self._send(200, png, "image/png")
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
            if name.endswith(".png") and os.path.isfile(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "image/png")
            elif name.endswith(".zip") and os.path.isfile(path):
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
        elif self.path == "/api/deck":
            # ChipDeck (0.1.9e, #94): the binder's contents — every
            # picture-riding thing on this machine, with its state.
            # (Loads its own config: this route sits above the
            # handler's shared cfg assignment.)
            self._send(200, deck_contents(load_config()))
        elif self.path.split("?")[0] == "/api/deck/file":
            # A Mesh pairing card's picture, for its ChipDeck
            # sleeve (chips ride /api/chips/file, packs ride
            # /api/rag/cartridge.png). Basename-jailed to the
            # cards folder, .png only.
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = os.path.basename((qs.get("name") or [""])[0])
            path = os.path.join(MESH_CARDS_DIR, name)
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
                "chips": [{"file": c["file"], "name": c["name"], "source": c.get("source"), "sourceKey": c.get("sourceKey"), "locallyEdited": bool(c.get("locallyEdited")), "unreadable": bool(c.get("unreadable")), "requirements": list(c.get("requirements") or [])} for c in local_chips()],
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
        elif self.path.split("?")[0] == "/api/update/check":
            # The Updater's real check: the newest GitHub release
            # on the install's channel against the VERSION file. A
            # check that cannot complete answers ok: False with
            # the reason — never a made-up "up to date".
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            chan = (qs.get("channel") or [""])[0]
            self._send(200, update_check_payload(
                load_config(), chan if chan in ("stable", "edge") else None))
        elif self.path == "/api/update/result":
            # The end-to-end apply's live record: its current step
            # while it runs (written by the bridge's worker, then by
            # the detached helper once the install takes the bridge
            # down), and afterwards the confirmed version before →
            # after — or the failed step, its reason, and the manual
            # fallback. The relaunched bridge serves the same file,
            # which is how the panel learns the outcome.
            self._send(200, update_result_payload())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        cfg = load_config()
        if self.path.split("?")[0] == "/__gate":
            # The gate page's form: a remote visitor proving the
            # code. Success sets the long-lived acceptance cookie
            # (a hash of the code — regenerate the code and every
            # cookie stops matching) and sends them to the door
            # they asked for. Failure serves the gate page again
            # with the reason, and nothing else.
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
            form = urllib.parse.parse_qs(raw)
            given = (form.get("code") or [""])[0].strip().upper()
            want = public_settings(cfg)["access_code"]
            if want and given == want.upper():
                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header(
                    "Set-Cookie",
                    PUBLIC_COOKIE + "=" + public_token(want)
                    + "; Max-Age=" + str(PUBLIC_COOKIE_MAX_AGE)
                    + "; Path=/; HttpOnly; SameSite=Lax",
                )
                self.send_header("Content-Length", "0")
                self.end_headers()
            else:
                self._send(
                    200,
                    gate_page_html(
                        "That code did not open the door - check the code on the DHD page of the machine Apex runs on, and try again."
                    ).encode(),
                    "text/html; charset=utf-8",
                )
            return
        # Build .86: /mesh/borrow is not served on this surface
        # (see do_GET) — the dedicated Mesh port is the only
        # lender door.
        if self._public_gate_blocks():
            self._send(403, {"error": "access code required"})
            return
        if self.path.split("?")[0] == "/mesh/lend/stop":
            # Instant-off (R4): a LOCAL dashboard action only. It
            # is never served on the DHD-forwarded surface — a
            # request the proxy carried in is refused here even
            # with a valid dashboard session, and no node signature
            # can reach it either (this route is behind the gate,
            # not the signature check).
            if (self.headers.get("X-Apex-Via") or "") == "dhd":
                self._send(403, {"ok": False, "error": "Stop lending now is a local action — it is not available through the DHD door."})
                return
            self._send(200, {"ok": True, "mesh": mesh_stop_lending((self.headers.get("X-Apex-Via") or "") == "dhd")})
            return
        if self.path == "/api/mesh/settings":
            # The Settings → System Mesh card's save. Persists the
            # block, sets identity up on first enable, and starts
            # or stops the dedicated Mesh door to match. Q1: lending
            # may be turned ON only in person — a save arriving
            # through the DHD proxy surface is refused for that one
            # change; turning anything OFF is allowed from anywhere
            # the operator is signed in.
            data = self._body()
            block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
            block = dict(block)
            borrow = block.get("borrow") if isinstance(block.get("borrow"), dict) else {}
            borrow = dict(borrow)
            lend = block.get("lend") if isinstance(block.get("lend"), dict) else {}
            lend = dict(lend)
            was_enabled = block.get("enabled") is True
            was_lending = lend.get("enabled") is True
            want_lending = bool(data.get("lendEnabled")) if "lendEnabled" in data else was_lending
            if want_lending and not was_lending and (self.headers.get("X-Apex-Via") or "") == "dhd":
                self._send(200, {"ok": False, "error": "Lending can only be turned on from this machine's own dashboard, in person — not through the DHD door. Turning it off works from anywhere."})
                return
            if "enabled" in data:
                block["enabled"] = bool(data.get("enabled"))
            if "nodeName" in data:
                block["nodeName"] = str(data.get("nodeName") or "")[:80]
            if "borrowEnabled" in data:
                borrow["enabled"] = bool(data.get("borrowEnabled"))
            if "graceMs" in data:
                borrow["graceMs"] = max(0, min(30000, _mesh_int(data.get("graceMs"), 2000)))
            if "lendEnabled" in data:
                lend["enabled"] = want_lending
            # Build 7 (#87, Fix F): the lending caps are operator
            # settings on the lending machine — share of each hour
            # (1–100%), borrowed generations an hour and per peer
            # an hour (1–10000 each). They persist in the lend
            # block and take effect on the next admission decision
            # and the next card/capability report, because both
            # read mesh_settings(load_config()) fresh — no bridge
            # restart. The shipped defaults (25 / 20 / 10) are
            # only the fallbacks for a missing or unparseable
            # value, here and in mesh_settings.
            if "maxSharePercent" in data:
                lend["maxSharePercent"] = max(1, min(100, _mesh_int(data.get("maxSharePercent"), 25)))
            if "maxGenerationsPerHour" in data:
                lend["maxGenerationsPerHour"] = max(1, min(10000, _mesh_int(data.get("maxGenerationsPerHour"), 20)))
            if "perPeerPerHour" in data:
                lend["perPeerPerHour"] = max(1, min(10000, _mesh_int(data.get("perPeerPerHour"), 10)))
            # Build 7 (Fix F2): the idle-only override rides the
            # same save. Admission already reads lend["idleOnly"]
            # on every request, so the flip is live at once; the
            # shipped default stays ON (a lender serves only
            # after idleAfterSeconds of quiet) until the operator
            # turns it off here.
            if "idleOnly" in data:
                lend["idleOnly"] = bool(data.get("idleOnly"))
            if "ledgerInBackup" in data:
                block["ledgerInBackup"] = bool(data.get("ledgerInBackup"))
            block["borrow"] = borrow
            block["lend"] = lend
            cfg["mesh"] = block
            if block.get("enabled") is True and not was_enabled:
                # Build 7 (#87): a node whose name was never set
                # sits "Unnamed" in every roster — at enable time,
                # a blank name takes the machine's hostname as its
                # default, persisted with this save. A name the
                # operator typed is never overwritten.
                if not str(block.get("nodeName") or "").strip():
                    block["nodeName"] = socket.gethostname()[:80]
                _ok, _err = mesh_ensure_identity(cfg)
                if not _ok:
                    self._send(200, {"ok": False, "error": _err})
                    return
                _ok, _err = mesh_ensure_cert()
                if not _ok:
                    self._send(200, {"ok": False, "error": _err})
                    return
                # Pick up the nodeId identity setup recorded — but
                # identity saves the config only when it writes a
                # NEW nodeId, so on a re-enable (identity already on
                # disk) the file still holds the pre-save block, and
                # reloading it wholesale would resurrect that block
                # and silently drop this save's change while still
                # answering ok: the master switch stayed off under
                # a "Saved." (field report, 0.1.8e Build 2 — the
                # first enable worked precisely because identity's
                # first write carried the change with it). The
                # operator's block is the change being saved; the
                # saved config contributes only the nodeId it holds.
                _saved = load_config().get("mesh")
                if isinstance(_saved, dict) and _saved.get("nodeId"):
                    block["nodeId"] = _saved["nodeId"]
                cfg["mesh"] = block
            save_config(cfg)
            if block.get("enabled") is True:
                mesh_start_listener()
                if not was_enabled:
                    # Build 7 (#87): enabling Mesh checks every
                    # paired peer at once, not at the health
                    # cadence's leisure.
                    mesh_probe_peers_soon()
            else:
                mesh_stop_listener()
            self._send(200, {"ok": True, "mesh": mesh_status_payload(load_config(), (self.headers.get("X-Apex-Via") or "") == "dhd")})
            return
        # Build 9 (#90): POST /api/mesh/peers — the paste-a-text-
        # card import — is REMOVED. Pairing is the PNG picture
        # only (the /api/mesh/peers/png route below); a request
        # to the retired path falls through to this handler's
        # not-found answer. Peers paired earlier are stored
        # records in config and are untouched by the removal.
        if self.path == "/api/mesh/peers/png":
            # Add a peer from a PNG picture card (Build 7, spec
            # section 13). The dashboard sends the picture's bytes
            # base64'd — from the file-upload control or a drag-
            # and-drop, both through the one client importer — and
            # the payload inside the picture goes through the same
            # card validation and the same add every pairing
            # passes: one parser, one pairing, the identical
            # peer record.
            # A picture with no readable payload, or a damaged
            # one, is refused with its specific reason — never a
            # silent no-op.
            data = self._body()
            raw = None
            try:
                raw = base64.b64decode(str(data.get("png") or ""), validate=True)
            except Exception:
                raw = None
            if not raw:
                self._send(200, {"ok": False, "error": "That upload did not arrive as a picture — try the upload again."})
                return
            if len(raw) > 8 * 1024 * 1024:
                self._send(200, {"ok": False, "error": "That file is far larger than a Mesh card picture — the cards are small PNGs. Check you picked the card file, and try again."})
                return
            peer, png_err = parse_mesh_card_png(raw)
            if peer is None:
                self._send(200, {"ok": False, "error": png_err})
                return
            aerr = mesh_add_peer(cfg, peer)
            if aerr:
                self._send(200, {"ok": False, "error": aerr})
                return
            mesh_probe_peers_soon()
            self._send(200, {"ok": True, "mesh": mesh_status_payload(load_config())})
            return
        if self.path == "/api/mesh/peers/remove":
            data = self._body()
            target = str(data.get("nodeId") or "")
            block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
            block = dict(block)
            borrow = block.get("borrow") if isinstance(block.get("borrow"), dict) else {}
            borrow = dict(borrow)
            peers = borrow.get("peers") if isinstance(borrow.get("peers"), list) else []
            borrow["peers"] = [p for p in peers if not (isinstance(p, dict) and str(p.get("nodeId") or "") == target)]
            block["borrow"] = borrow
            cfg["mesh"] = block
            save_config(cfg)
            self._send(200, {"ok": True, "mesh": mesh_status_payload(load_config())})
            return
        if self.path == "/api/mesh/peers/can-borrow":
            # The borrow-side toggle for one paired peer (Build 7,
            # #87): whether THIS machine borrows from that peer.
            # It no longer gates the peer's inbound requests —
            # pairing is that side's consent (mesh_authenticate).
            data = self._body()
            target = str(data.get("nodeId") or "")
            block = cfg.get("mesh") if isinstance(cfg.get("mesh"), dict) else {}
            block = dict(block)
            borrow = block.get("borrow") if isinstance(block.get("borrow"), dict) else {}
            borrow = dict(borrow)
            peers = borrow.get("peers") if isinstance(borrow.get("peers"), list) else []
            new_peers = []
            for p in peers:
                if isinstance(p, dict) and str(p.get("nodeId") or "") == target:
                    p = dict(p)
                    p["canBorrow"] = bool(data.get("canBorrow"))
                new_peers.append(p)
            borrow["peers"] = new_peers
            block["borrow"] = borrow
            cfg["mesh"] = block
            save_config(cfg)
            self._send(200, {"ok": True, "mesh": mesh_status_payload(load_config())})
            return
        if self.path == "/api/settings/updater-channel":
            # The Updater's channel switch (build .83): persist
            # the operator's Stable / Edge choice in the config's
            # updater block. Checks and the apply path both read
            # it from there, so the choice survives restarts and
            # a remote (DHD) session flips the same switch.
            data = self._body()
            chan = data.get("channel")
            if chan not in ("stable", "edge"):
                self._send(200, {"ok": False, "error": "The channel must be 'stable' or 'edge'."})
                return
            block = cfg.get("updater") if isinstance(cfg.get("updater"), dict) else {}
            block = dict(block)
            block["channel"] = chan
            # Build 2: this save is the operator's own act, so it
            # stamps the choice as explicit — the stamp is what
            # separates a chosen channel from one the config
            # merely inherited (see updater_channel_explicit).
            block["channelExplicit"] = True
            cfg["updater"] = block
            save_config(cfg)
            self._send(200, {"ok": True, "channel": chan, "channelExplicit": True})
            return
        if self.path == "/api/settings/public":
            # The Local server toggle itself (build .61 — one
            # action): persist the choice in the config block AND
            # restart this bridge so the choice takes effect. The
            # restart rides the exit-75 handshake: the request is
            # recorded in the block, the response goes out, and this
            # process exits 75 — the launcher's supervisor relaunches
            # it, and the new bridge binds per the saved choice and
            # verifies its own bind against it. The running bridge
            # never hot-swaps its bind. Flipping to the state already
            # live needs no restart and confirms on the spot.
            data = self._body()
            block = cfg.get("public_server") if isinstance(cfg.get("public_server"), dict) else {}
            block = dict(block)
            block["enabled"] = bool(data.get("enabled"))
            cfg["public_server"] = block
            ensure_access_code(cfg)
            save_config(cfg)
            want_public = bool(data.get("enabled"))
            live_public = ACTIVE_BIND_HOST == "0.0.0.0"
            if want_public == live_public:
                set_public_restart(cfg, "confirmed", "", "The bridge that answers already runs this choice — no restart was needed.")
                self._send(200, {"ok": True, "publicServer": public_state_payload(load_config(), self._client_is_loopback())})
            else:
                set_public_restart(cfg, "restarting", "restart", "Restarting the bridge…")
                self._send(200, {"ok": True, "publicServer": public_state_payload(load_config(), self._client_is_loopback())})
                schedule_bridge_restart()
        elif self.path == "/api/dhd/toggle":
            # The DHD master switch (build .74) — one click: the
            # choice is saved and the whole ladder runs in this
            # process (certificate, proxy, self-check) with no
            # bridge restart, because the proxy is threads, not the
            # bridge's own bind. The one exception: if the Local
            # server currently binds this bridge publicly, DHD mode
            # requires the bridge on loopback only, so enabling
            # records the choice and rides the exit-75 supervisor
            # restart — the relaunched bridge binds loopback and
            # brings the proxy up in main(). A failed step names
            # itself and leaves the previous state untouched.
            data = self._body()
            want = bool(data.get("enabled"))
            if not want:
                dhd_save(cfg, {"enabled": False})
                ensure_access_code(cfg)
                cfg = load_config()
                dhd_stop_proxy()
                DHD_STATE["last_error"] = ""
                self._send(200, {"ok": True, "dhd": dhd_state_payload(cfg, self._client_is_loopback())})
            else:
                # Enabling is an operation: the page and chat
                # render the same persisted step card while the
                # bridge runs prerequisites, certificate, proxy,
                # and reachability — no model work is involved.
                _op_id = dhd_start_enable_operation("page", str(data.get("sudo_password") or data.get("sudoPassword") or ""))
                self._send(200, {"ok": True, "operationId": _op_id, "operation": op_snapshot(_op_id), "dhd": dhd_state_payload(load_config(), self._client_is_loopback())})
        elif self.path == "/api/dhd/install":
            # The safety-net install action: install the named
            # missing prerequisites (or every missing installable
            # one) through the detected distro family's package
            # step, then release any DHD enable operation waiting
            # on them so it continues automatically. An install
            # failure returns the step's exact manual commands.
            data = self._body()
            _pieces = data.get("pieces") if isinstance(data.get("pieces"), list) else None
            _result = dhd_install_prereqs(_pieces, str(data.get("sudo_password") or data.get("sudoPassword") or ""))
            _failed = [r for r in _result["results"] if not r["ok"]]
            if _failed:
                _commands = []
                for r in _failed:
                    _commands.extend(r.get("commands") or [])
                _detail = " ".join(r.get("detail", "") for r in _failed)
                _dhd_release_waiting_ops(False, _detail, _commands)
                self._send(200, {"ok": False, "install": _result, "commands": _commands, "dhd": dhd_state_payload(load_config(), self._client_is_loopback())})
            else:
                _dhd_release_waiting_ops(True, "Prerequisites installed.")
                _op_id = None
                _cfg_now = load_config()
                if dhd_settings(_cfg_now)["enabled"] and not DHD_STATE.get("running"):
                    _op_id = dhd_start_enable_operation("install", str(data.get("sudo_password") or data.get("sudoPassword") or ""))
                self._send(200, {"ok": True, "install": _result, "operationId": _op_id, "operation": op_snapshot(_op_id) if _op_id else op_latest("dhd-enable"), "dhd": dhd_state_payload(load_config(), self._client_is_loopback())})
        elif self.path == "/api/dhd/domain":
            # The optional custom domain: free-form, saved in the
            # dhd block so it survives restarts and updates. When
            # DHD is live, saving a domain starts the certificate
            # step in the background (ACME can take a few seconds);
            # the door keeps answering on the current certificate
            # meanwhile and the state reads certificate-pending
            # until the real one is installed.
            data = self._body()
            domain = str(data.get("domain") or "").strip().lower()
            domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
            dhd_save(cfg, {"domain": domain})
            cfg = load_config()
            if domain and dhd_settings(cfg)["enabled"] and DHD_STATE["running"]:
                threading.Thread(target=lambda: dhd_bring_up(load_config()), daemon=True).start()
            self._send(200, {"ok": True, "dhd": dhd_state_payload(cfg, self._client_is_loopback())})
        elif self.path == "/api/dhd/cert":
            # The certificate step on its own: obtain (or renew)
            # the saved domain's certificate now, via the built-in
            # ACME client, and reload the proxy with it.
            cfg_now = load_config()
            ds_now = dhd_settings(cfg_now)
            if not ds_now["domain"]:
                self._send(200, {"ok": False, "error": "No domain is saved yet - add one first.", "dhd": dhd_state_payload(cfg_now, self._client_is_loopback())})
            else:
                ok = dhd_bring_up(cfg_now)
                self._send(200, {"ok": ok, "dhd": dhd_state_payload(load_config(), self._client_is_loopback())})
        elif self.path == "/api/settings/public/restart":
            # The row's Restart bridge control: the retry/fallback
            # for a saved choice that is not live (a failed restart,
            # or a pending state left by an older build). Same flow
            # as the toggle: record the request, exit 75, let the
            # supervisor relaunch, and let the new bridge verify.
            cfg_now = load_config()
            if not public_state_payload(cfg_now, True)["pending"]:
                self._send(200, {"ok": True, "publicServer": public_state_payload(cfg_now, self._client_is_loopback())})
            else:
                set_public_restart(cfg_now, "restarting", "restart", "Restarting the bridge…")
                self._send(200, {"ok": True, "publicServer": public_state_payload(load_config(), self._client_is_loopback())})
                schedule_bridge_restart()
        elif self.path == "/api/settings/public/regenerate":
            # A fresh code. Because the acceptance cookie is a
            # hash of the code, this invalidates every client the
            # old code let in — they will be asked again.
            block = cfg.get("public_server") if isinstance(cfg.get("public_server"), dict) else {}
            block = dict(block)
            block["access_code"] = generate_access_code()
            if "enabled" not in block:
                block["enabled"] = False
            cfg["public_server"] = block
            save_config(cfg)
            self._send(200, {"ok": True, "publicServer": public_state_payload(load_config(), self._client_is_loopback())})
        elif self.path == "/api/shell":
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
            # Starts the end-to-end apply: the worker downloads,
            # verifies (gzip-tolerant), and stages the release
            # package under updates/<tag>/package, then a detached
            # helper runs the staged installer and relaunches the
            # app. Progress and outcome are read back through
            # GET /api/update/result.
            self._send(200, update_apply_payload(cfg))
        elif self.path == "/api/downloads/save":
            # The dashboard's download-save flow (build .48): the
            # bytes behind a download click inside the desktop shell
            # (chip .png, export ZIP), written into the operator's
            # Downloads folder under a sanitized name — the shell's
            # webview cannot save files the way a browser does.
            self._send(200, save_download_payload(self._body()))
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
            memory_mode = data.get("memory_mode") if data.get("memory_mode") in ("autonomous", "ask", "trigger") else "autonomous"
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
                _reply = chip_shelf_reply("./")
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
            # "./name args..." runs a chip the way ./ runs a
            # program (0.1.9e, issue #97) — the composer's pill
            # shelf is retired, and this is the keyboard way in.
            # Bare "./" answers with the shelf. The latch decides
            # collisions: a $-forced line or a CLI-latched composer
            # never reaches here, so under the latch "./x" is still
            # the shell's own.
            _lt = (last or "").strip()
            if (
                _lt.startswith("./")
                and not _lt.startswith("$")
                and chat_mode != "cli"
            ):
                _rest = _lt[2:]
                if not _rest.strip():
                    _reply = chip_shelf_reply("./")
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
                _chip, _cargs = resolve_chip_invocation(_rest, local_chips())
                if isinstance(_cargs, list):
                    if _cargs:
                        _reply = (
                            "That name fits more than one chip on this machine: "
                            + ", ".join(c["name"] for c in _cargs)
                            + " — say which one, as ./<name>."
                        )
                    else:
                        _reply = (
                            "No chip by that name is loaded on this machine. "
                            + chip_shelf_reply("./")
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
            # DHD operations from chat: a direct request to turn
            # DHD on or off is deterministic bridge work, decided
            # before any model or CLI route. Enabling starts the
            # same operation the DHD page uses; the reply carries
            # its snapshot and the dashboard renders the live card
            # in this thread. No model generation happens while
            # the operation runs.
            _dhd_intent = dhd_chat_intent(last or "")
            if _dhd_intent == "enable":
                if dhd_settings(cfg)["enabled"] and DHD_STATE.get("running"):
                    _reply = _dhd_on_summary(dhd_state_payload(cfg, True))
                    _op = None
                else:
                    _op_id = dhd_start_enable_operation("chat", sudo_password)
                    _op = op_snapshot(_op_id)
                    _reply = "Starting DHD now. The card below is the live record — prerequisites, certificate, proxy, and the reachability check — and it stays in this thread when it finishes."
                payload = {
                    "reply": _reply, "exec": None, "mode": "operation",
                    "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                    "operation": _op,
                }
                if data.get("speak"):
                    payload["spoken"] = speak_reply(_reply, cfg)
                self._send(200, payload)
                return
            if _dhd_intent == "disable":
                dhd_save(cfg, {"enabled": False})
                ensure_access_code(cfg)
                dhd_stop_proxy()
                DHD_STATE["last_error"] = ""
                _reply = "DHD is off. Apex answers only on this machine and your home network again; the domain and certificate stay saved for the next one-click start."
                payload = {
                    "reply": _reply, "exec": None, "mode": "operation",
                    "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                    "operation": None,
                }
                if data.get("speak"):
                    payload["spoken"] = speak_reply(_reply, cfg)
                self._send(200, payload)
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
            # Memory from chat — the trigger (build .81, issue
            # #72): deterministic bridge work beside Vault filing,
            # decided before the model route and before the
            # command-line fallback, so it works with or without
            # the model connected. The fact rides the payload back
            # as data; the dashboard files it into her memory
            # store and draws the receipt in the thread. A
            # secret-shaped payload is refused in words and
            # nothing is written.
            _mtrig = memory_trigger(last or "")
            if _mtrig is not None:
                _mfact = ""
                if _mtrig[0] == "fact":
                    _mfact = normalize_memory_fact(_mtrig[1])
                else:
                    for _pm in reversed(messages[:-1]):
                        if isinstance(_pm, dict) and _pm.get("role") == "user" and (_pm.get("content") or "").strip():
                            _mfact = normalize_memory_fact(_pm.get("content"))
                            break
                _mlive = "running" if llamafile_alive(endpoint) else "stopped"
                if not _mfact:
                    _reply = "Point me at the thing itself — say it first and then \"remember this\", or say \"remember:\" and the fact, and I'll write it down word for word and show you the receipt."
                    payload = {"reply": _reply, "exec": None, "mode": "model", "llamafile": _mlive}
                elif memory_looks_secret(_mfact):
                    _reply = "I didn't save that — it looks like a secret, and secrets never go into my memory, not even when you ask me directly. If it needs keeping, it belongs somewhere built for secrets, not in the memory I carry into every conversation."
                    payload = {"reply": _reply, "exec": None, "mode": "model", "llamafile": _mlive, "memoryRefused": True}
                else:
                    _reply = "Written down. The receipt below is exactly what I saved — word for word — and Undo takes it back out if I got it wrong."
                    payload = {"reply": _reply, "exec": None, "mode": "model", "llamafile": _mlive, "memorySaves": [{"text": _mfact, "origin": "trigger", "key": memory_fact_key(_mfact), "proposed": False}]}
                if data.get("speak"):
                    payload["spoken"] = speak_reply(_reply, cfg)
                self._send(200, payload)
                return
            _vfiling = re.search(r"(?:file|write|save|make|take)\s+(?:a\s+|this\s+)?note\b", (last or ""), re.I) or re.search(r"\bnote\s+(?:this|that)\s+down\b", (last or ""), re.I) or re.match(r"\s*note\s*:", (last or ""), re.I)
            if _vfiling:
                _vpath, _verr = vault_file_from_chat(last or "", messages)
                if _vpath:
                    _own = _vpath.startswith("Operator/")
                    payload = {
                        "reply": ("Filed it on your side of the desk — **" + _vpath + "** in the Vault. You can edit it there any time; I won't touch it again unless you ask.") if _own else ("Filed it on my side of the desk — **" + _vpath + "** in the Vault. It's mine to keep faithfully now: dated, in my own words, and I'll name it when it informs an answer."),
                        "exec": None,
                        "mode": "model",
                        "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                    }
                    if data.get("speak"):
                        payload["spoken"] = speak_reply(payload["reply"], cfg)
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
            _vhits = vault_search(last or "", 2)
            _vmentions = bool(re.search(r"\b(vault|notes?)\b", (last or ""), re.I))
            if _vhits and not _vmentions and _vhits[0]["score"] < 6:
                _vhits = []
            if _vhits:
                _vctx = "\n\n".join("[Vault · " + h["path"] + "] " + h["excerpt"] for h in _vhits)
                messages = messages + [{
                    "role": "system",
                    "content": "Material from the shared Vault — the operator's and your own notes. Use it where it answers the question, in your own words. Do not name or cite the sources in your reply — the dashboard shows them under your message on its own:\n" + _vctx,
                }]
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
                "content": persona_prompt(cfg, str(data.get("operator_name") or ""), memory_mode),
            }] + messages
            try:
                model = cfg.get("live", {}).get("model_name") or "navi"
                # Navi Mesh (Ring 1): the model route is the ONLY
                # route that borrows — CLI mode, chips, and every
                # deterministic route above never do. The exact
                # assembled messages ride (persona/Vault/RAG/history
                # assembly stays borrower-side), and everything
                # below — citation strip, memory markers, speech —
                # stays borrower-side on the returned text,
                # unchanged. meshLocal is the per-request escape:
                # when the operator set it, no borrow is attempted
                # at all.
                _mesh_payload = None
                reply = None
                if not data.get("meshLocal"):
                    _ms = mesh_settings(cfg)
                    if _ms["enabled"] and _ms["borrow"]["enabled"] and _ms["borrow"]["peers"]:
                        reply, _mesh_payload = mesh_try_borrow(messages, cfg, _ms)
                if reply is None:
                    with MESH_LOCK:
                        MESH_STATE["local_gen"] += 1
                    try:
                        reply = llamafile_chat(messages, endpoint, model)
                    finally:
                        with MESH_LOCK:
                            MESH_STATE["local_gen"] = max(0, MESH_STATE["local_gen"] - 1)
                            MESH_STATE["last_local_done"] = time.time()
                # The reply text stays citation-free (see
                # strip_citation_footer): sources are data, drawn
                # as pills under this one message by the dashboard.
                # Only a turn whose question actually retrieved pack
                # material carries any — once the conversation moves
                # on, there is nothing to show.
                reply = strip_citation_footer(reply)
                # Memory from chat — her own call (build .81,
                # #72): her [[remember: …]] markers come out of
                # the reply before it is shown or spoken, and the
                # saves ride the payload back as data for the
                # dashboard to file and receipt.
                reply, _msaves, _mrefused = extract_memory_markers(reply, memory_mode)
                payload = {"reply": reply, "exec": exec_block, "mode": "model", "llamafile": "running"}
                if _mesh_payload:
                    payload["mesh"] = _mesh_payload
                if _msaves:
                    payload["memorySaves"] = _msaves
                if _mrefused:
                    payload["memoryRefused"] = True
                if _hits:
                    _srcs = []
                    for h in _hits:
                        _s = {"pack": h["pack"], "document": h["document"]}
                        if _s not in _srcs:
                            _srcs.append(_s)
                    payload["rag"] = _srcs
                if _vhits:
                    _all = payload.get("rag") or []
                    for h in _vhits:
                        _s = {"pack": "Vault", "document": h["path"]}
                        if _s not in _all:
                            _all.append(_s)
                    payload["rag"] = _all
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
        elif self.path == "/api/vault/save":
            # Create or update a note (the editor's autosave lands
            # here). Jailed to the vault; frontmatter rides as text.
            data = self._body()
            rel = vault_join(str(data.get("path") or ""))
            if not rel or not rel.lower().endswith(".md"):
                self._send(200, {"ok": False, "error": "That path escapes the vault — notes live inside the vault folder only, as .md files."})
            else:
                vault_write(rel, str(data.get("content") or "")[:200000])
                self._send(200, {"ok": True})
        elif self.path == "/api/vault/delete":
            data = self._body()
            rel = vault_join(str(data.get("path") or ""))
            if not rel:
                self._send(200, {"ok": False, "error": "That path escapes the vault."})
            elif not os.path.isfile(vault_fs_path(rel)):
                # Never a silent no-op (build .73): if the note isn't
                # on disk, the operator hears about it in plain words.
                self._send(200, {"ok": False, "error": "That note no longer exists — it may have been moved or deleted outside the app. The tree has been refreshed."})
            else:
                os.remove(vault_fs_path(rel))
                self._send(200, {"ok": True})
        elif self.path == "/api/vault/move":
            # Rename / drag-and-drop move. Never overwrites.
            data = self._body()
            src = vault_join(str(data.get("from") or ""))
            dst = vault_join(str(data.get("to") or ""))
            if not src or not dst or not dst.lower().endswith(".md"):
                self._send(200, {"ok": False, "error": "That path escapes the vault — notes live inside the vault folder only, as .md files."})
            elif os.path.exists(vault_fs_path(dst)):
                self._send(200, {"ok": False, "error": "A note already exists at " + dst + " — pick another name."})
            elif not os.path.isfile(vault_fs_path(src)):
                self._send(200, {"ok": False, "error": "That note no longer exists."})
            else:
                parent = os.path.dirname(vault_fs_path(dst))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                os.replace(vault_fs_path(src), vault_fs_path(dst))
                self._send(200, {"ok": True})
        elif self.path == "/api/vault/folder":
            data = self._body()
            rel = vault_join(str(data.get("path") or ""))
            if not rel:
                self._send(200, {"ok": False, "error": "That folder path escapes the vault."})
            else:
                os.makedirs(vault_fs_path(rel), exist_ok=True)
                self._send(200, {"ok": True})
        elif self.path == "/api/vault/delete-folder":
            data = self._body()
            rel = vault_join(str(data.get("path") or ""))
            if not rel:
                self._send(200, {"ok": False, "error": "That folder path escapes the vault."})
            else:
                full = vault_fs_path(rel)
                count = 0
                if os.path.isdir(full):
                    for base, dirs, files in os.walk(full):
                        count += len([f for f in files if f.lower().endswith(".md")])
                    shutil.rmtree(full)
                self._send(200, {"ok": True, "deletedNotes": count})
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
                    "glyph": str(data.get("glyph") or "")[:40],
                    "version": str(data.get("version") or "")[:40],
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
        elif self.path == "/api/rag/export-png":
            # Export as a knowledge cartridge (issue #93): the pack
            # as ONE picture in rag-exports/, beside the ZIP export.
            # Past the size ceiling the refusal is honest — the ZIP
            # stays the way to carry a big pack — and nothing is
            # truncated to fit.
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            payload = rag_cartridge_payload(slug)
            if payload is None:
                self._send(200, {"ok": False, "error": "That pack is not in rag-packs/.", "file": None})
                return
            payload["version"] = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            png = build_rag_cartridge_png(payload)
            if len(png) > RAG_CARTRIDGE_MAX_BYTES:
                self._send(200, {"ok": False, "error": "This pack is too big for a picture — its cartridge would run " + str(len(png)) + " bytes against the " + str(RAG_CARTRIDGE_MAX_BYTES) + "-byte ceiling. Use the ZIP export for this one; nothing was written.", "file": None})
                return
            os.makedirs(RAG_EXPORTS_DIR, exist_ok=True)
            fname = slug + "-cartridge.png"
            with open(os.path.join(RAG_EXPORTS_DIR, fname), "wb") as f:
                f.write(png)
            self._send(200, {"ok": True, "error": None, "file": fname, "size": len(png)})
        elif self.path == "/api/rag/install-cartridge":
            # Install a pack from its picture alone (issue #93):
            # the dashboard sends the picture's bytes base64'd;
            # the payload validates and installs through the one
            # cartridge path, index built locally at install.
            data = self._body()
            try:
                raw = base64.b64decode(str(data.get("png") or ""), validate=True)
            except Exception:
                raw = None
            if not raw:
                self._send(200, {"ok": False, "error": "That upload did not arrive as a picture — try the upload again."})
                return
            if len(raw) > RAG_CARTRIDGE_MAX_BYTES:
                self._send(200, {"ok": False, "error": "That file is larger than a knowledge cartridge may be (" + str(RAG_CARTRIDGE_MAX_BYTES) + " bytes) — nothing was installed."})
                return
            payload, perr = parse_rag_cartridge_png(raw)
            if payload is None:
                self._send(200, {"ok": False, "error": perr})
                return
            slug, ierr = install_rag_cartridge(payload)
            if slug is None:
                self._send(200, {"ok": False, "error": ierr})
                return
            self._send(200, {"ok": True, "error": None, "slug": slug})
        elif self.path == "/api/rag/publish":
            # Publish to GitHub: upload the export's exact file set
            # to a repo on the signed-in account (created when
            # missing, navi-rag topic applied), and — since
            # 0.1.9e — the tag and the PUBLISHED release too,
            # with the knowledge cartridge attached. Publish
            # does everything; there is no manual release step.
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                files = rag_repo_files(slug, version)
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e)})
            else:
                index = _rag_pack_index(slug) or {}
                repo_name = str(data.get("repo_name") or "").strip() or (index.get("name") or slug)
                # The knowledge cartridge rides along: at the repo
                # root as the pack's picture, and attached to the
                # release. A pack too big for a picture publishes
                # without one, and says so in the result.
                asset_skip = None
                cart_name = slug + "-cartridge.png"
                cart_png = None
                try:
                    cart_png = build_rag_cartridge_png(rag_cartridge_payload(slug))
                    if len(cart_png) > RAG_CARTRIDGE_MAX_BYTES:
                        asset_skip = ("The pack is too big for a picture ("
                                      + str(len(cart_png)) + " bytes against the "
                                      + str(RAG_CARTRIDGE_MAX_BYTES) + "-byte ceiling), so the release carries no cartridge — the files and documents are all there. The ZIP export carries the pack whole.")
                        cart_png = None
                except Exception as e:
                    cart_png = None
                    asset_skip = "The knowledge cartridge could not be built (" + str(e) + "), so the release carries no cartridge — the files and documents are all there."
                if cart_png:
                    files = files + [(cart_name, cart_png)]
                _rreadme = next((d for a, d in files if a == "README.md"), "")
                release = {
                    "version": version,
                    "title": (index.get("name") or slug) + " v" + version.lstrip("v"),
                    "notes": _rreadme if isinstance(_rreadme, str) else "",
                    "assetName": cart_name if cart_png else "",
                    "assetData": cart_png,
                }
                result = github_publish_files(repo_name, files, "navi-rag", index.get("description") or "", release)
                if asset_skip and result.get("ok"):
                    result["assetSkipped"] = asset_skip
                self._send(200, result)
        elif self.path == "/api/rag/readme":
            # The effective README for the editor: the operator's
            # saved edit when there is one, else the generated page.
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                files = rag_repo_files(slug, version)
                readme = next((d for a, d in files if a == "README.md"), "")
                self._send(200, {"ok": True, "error": None, "readme": readme if isinstance(readme, str) else "", "edited": rag_readme_override(slug) is not None})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e), "readme": "", "edited": False})
        elif self.path == "/api/rag/readme-save":
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            text = str(data.get("readme") or "")
            if _rag_pack_index(slug) is None:
                self._send(200, {"ok": False, "error": "That pack is not in rag-packs/."})
            elif len(text) > 200000:
                self._send(200, {"ok": False, "error": "That README is too long to keep (200,000 characters max)."})
            else:
                with open(os.path.join(RAG_PACKS_DIR, slug, ".readme-override"), "w") as f:
                    f.write(text)
                self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/rag/readme-restore":
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            try:
                os.remove(os.path.join(RAG_PACKS_DIR, slug, ".readme-override"))
            except Exception:
                pass
            self._send(200, {"ok": True, "error": None})
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
        elif self.path == "/api/chips/publish":
            # Publish to GitHub: the chip counterpart of the pack
            # publish — same loop, navi-chips topic.
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                chip = load_local_chip(fname)
                files = build_chip_repo_files(chip, version)
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e)})
            else:
                repo_name = str(data.get("repo_name") or "").strip() or chip.get("name") or ""
                _png = next(((a, d) for a, d in files if a.endswith(".png") and isinstance(d, (bytes, bytearray))), (None, None))
                _readme = next((d for a, d in files if a == "README.md"), "")
                release = {
                    "version": version,
                    "title": (chip.get("name") or "Chip") + " v" + version.lstrip("v"),
                    "notes": _readme if isinstance(_readme, str) else "",
                    "assetName": _png[0] or "",
                    "assetData": _png[1],
                }
                result = github_publish_files(repo_name, files, "navi-chips", chip.get("description") or "", release)
                self._send(200, result)
        elif self.path == "/api/chips/readme":
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                chip = load_local_chip(fname)
                files = build_chip_repo_files(chip, version)
                readme = next((d for a, d in files if a == "README.md"), "")
                self._send(200, {"ok": True, "error": None, "readme": readme if isinstance(readme, str) else "", "edited": bool(chip.get("readme"))})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e), "readme": "", "edited": False})
        elif self.path == "/api/chips/readme-save":
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            text = str(data.get("readme") or "")
            if len(text) > 200000:
                self._send(200, {"ok": False, "error": "That README is too long to keep (200,000 characters max)."})
            else:
                try:
                    save_local_chip_readme(fname, text)
                    self._send(200, {"ok": True, "error": None})
                except Exception as e:
                    self._send(200, {"ok": False, "error": str(e)})
        elif self.path == "/api/chips/readme-restore":
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            try:
                save_local_chip_readme(fname, None)
                self._send(200, {"ok": True, "error": None})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e)})
        elif self.path == "/api/deck/install":
            # Drop-to-install on ChipDeck (0.1.9e, #94): one door
            # for every picture — the payload keyword inside the
            # PNG says what it is, and each kind installs through
            # its own kind's one path (chip picture install, the
            # knowledge-cartridge path, the Mesh card pairing).
            data = self._body()
            try:
                raw = base64.b64decode(str(data.get("png") or ""), validate=True)
            except Exception:
                raw = None
            if not raw:
                self._send(200, {"ok": False, "error": "That upload did not arrive as a picture — try the upload again."})
                return
            keys = _png_text_keywords(raw)
            if "navi-mesh-card" in keys:
                peer, perr = parse_mesh_card_png(raw)
                if peer is None:
                    self._send(200, {"ok": False, "error": perr})
                    return
                err = mesh_add_peer(cfg, peer)
                if err:
                    self._send(200, {"ok": False, "error": err})
                    return
                # The card's picture joins the binder's card folder
                # (the backup's naming: peer-<node>.png) — pairing
                # through the Deck keeps the picture it paired from,
                # exactly as a backup restore lands it.
                try:
                    os.makedirs(MESH_CARDS_DIR, exist_ok=True)
                    cname = "peer-" + str(peer.get("nodeId") or "card")[:12] + ".png"
                    with open(os.path.join(MESH_CARDS_DIR, cname), "wb") as f:
                        f.write(raw)
                except Exception:
                    pass
                mesh_probe_peers_soon()
                self._send(200, {"ok": True, "error": None, "kind": "mesh", "name": peer.get("name") or ""})
                return
            if "navi-rag" in keys:
                payload, perr = parse_rag_cartridge_png(raw)
                if payload is None:
                    self._send(200, {"ok": False, "error": perr})
                    return
                slug, ierr = install_rag_cartridge(payload)
                if slug is None:
                    self._send(200, {"ok": False, "error": ierr})
                    return
                self._send(200, {"ok": True, "error": None, "kind": "rag", "name": payload.get("name") or slug})
                return
            if "navi-chip" in keys:
                payload = parse_cartridge_png(raw)
                if payload is None:
                    self._send(200, {"ok": False, "error": "That picture's chip data could not be read — it may have been recompressed on its way here, which strips the data out. Send the original file inside a .zip instead."})
                    return
                slug = chip_slug(payload["name"])
                filename = slug + ".png"
                if os.path.isfile(os.path.join(CHIPS_DIR, filename)):
                    self._send(200, {"ok": False, "error": payload["name"] + " is already on this machine — its picture is in the chips folder."})
                    return
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, filename), "wb") as f:
                    f.write(raw)
                rows = [r for r in load_chip_installs() if r.get("full_name") != "local/" + slug]
                rows.append({
                    "full_name": "local/" + slug,
                    "name": payload["name"],
                    "html_url": "",
                    "installed_tag": None,
                    "installed_ref": "chip " + filename + " (from its picture)",
                    "installed_pushed_at": None,
                    "installed_at": _now_iso(),
                    "local_file": filename,
                    "requirements": list(payload.get("requirements") or []),
                })
                save_chip_installs(rows)
                self._send(200, {"ok": True, "error": None, "kind": "chip", "name": payload["name"], "version": str(payload.get("version") or "")})
                return
            self._send(200, {"ok": False, "error": "That picture carries nothing the binder can slot in — no chip, knowledge cartridge, or Mesh card data inside it. A picture that was recompressed on its way here loses its data while looking the same; send the original inside a .zip."})
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
                record["requirements"] = list(payload.get("requirements") or [])
                rows.append(record)
                save_chip_installs(rows)
                # Build .86 (issue #79): the install verifies
                # itself — re-run the folder scan and answer ok
                # only if the chip actually appears in it. A chip
                # that landed on disk but does not list is named
                # as such, with the reason, and its record is
                # taken back so Installed never claims it.
                landed = next((c for c in local_chips() if c.get("file") == filename), None)
                if landed is None or landed.get("unreadable"):
                    rows = [r for r in rows if r is not record]
                    save_chip_installs(rows)
                    if landed is None and not os.path.isfile(os.path.join(CHIPS_DIR, filename)):
                        why = "the chip file is missing from the chips folder"
                    else:
                        why = "its cartridge could not be read back (unparseable cartridge)"
                    self._send(200, {"ok": False, "error": "The chip landed on disk as " + filename + " but does not list: " + why + ". Nothing was kept as installed."})
                    return
                self._send(200, {"ok": True, "error": None, "version": str(payload.get("version") or "")})
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
                fresh["requirements"] = list(payload.get("requirements") or [])
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
            elif full.startswith("local/"):
                # 0.1.9e audit fix: a chip dropped into chips/ by
                # hand has NO install record, so the record-driven
                # delete above removed nothing while the UI said
                # "Deleted" — the cartridge stayed on the shelf.
                # A local/ delete names the file by its stem; take
                # the picture with the (absent) record.
                _stem = re.sub(r"[^a-z0-9-]+", "-", full[len("local/"):].lower()).strip("-")
                if _stem:
                    try:
                        os.remove(os.path.join(CHIPS_DIR, _stem + ".png"))
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
                    "glyph": str(data.get("glyph") or "")[:40],
                    "version": str(data.get("version") or "")[:40],
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


def pid_cmdline(pid):
    # The process's command line as one line of text, read from
    # /proc — used to NAME a port holder in startup messages
    # (build .91), never to decide anything about it.
    try:
        with open("/proc/" + str(pid) + "/cmdline", "rb") as f:
            raw = f.read()
        return " ".join(part.decode("utf-8", "replace") for part in raw.split(bytes([0]))).strip()
    except Exception:
        return ""


def port_holder_pid(port):
    # The PID holding the LISTEN socket on the port, resolved from
    # /proc alone (build .91, issue #91): names a holder that
    # answers NOTHING — a bridge frozen or stuck so the status
    # probe and the page-title probe both come back empty, the
    # state a wedged update leaves behind once the pid file is
    # gone. Returns None when the port is free or the holder
    # cannot be resolved.
    inodes = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                rows = f.read().splitlines()[1:]
        except Exception:
            continue
        for row in rows:
            parts = row.split()
            if len(parts) > 9 and parts[3] == "0A":
                try:
                    if int(parts[1].rsplit(":", 1)[1], 16) == port:
                        inodes.add(parts[9])
                except Exception:
                    pass
    if not inodes:
        return None
    targets = set("socket:[" + ino + "]" for ino in inodes)
    try:
        names = os.listdir("/proc")
    except Exception:
        return None
    for name in names:
        if not name.isdigit():
            continue
        try:
            fds = os.listdir("/proc/" + name + "/fd")
        except Exception:
            continue
        for fd in fds:
            try:
                if os.readlink("/proc/" + name + "/fd/" + fd) in targets:
                    return int(name)
            except Exception:
                pass
    return None


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
        if holder is None:
            # Nothing answers on the port — but something may still
            # HOLD it: a bridge frozen or stuck so it accepts no
            # requests at all (build .91, the wedged-update state,
            # its pid file long gone). Resolve the holder from the
            # socket itself and name it, so the bind loop's wait —
            # and its failure message, if it comes to that — is
            # about a named process, not a shrug.
            _hp = port_holder_pid(port)
            if _hp:
                print("Port " + str(port) + " is held by process "
                      + str(_hp) + " ("
                      + (pid_cmdline(_hp) or "unknown command")
                      + "), which is not answering — waiting for it "
                      "to step aside.", flush=True)
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
    # Local server (build .59): the saved choice picks the bind
    # for THIS process, once, here. ON binds every interface so
    # the LAN can reach the port; OFF keeps the loopback-only
    # bind Apex has always had. Internal callers poll 127.0.0.1,
    # which answers on either bind, so nothing else changes.
    if dhd_settings(cfg)["enabled"]:
        # DHD mode (build .74): the bridge NEVER binds publicly -
        # Apex's own proxy is the only public face, forwarding to
        # this loopback bind. This wins over the Local server
        # choice, which is about the LAN door on the bridge port.
        ensure_access_code(cfg)
        ACTIVE_BIND_HOST = "127.0.0.1"
    elif public_settings(cfg)["enabled"]:
        ensure_access_code(cfg)
        ACTIVE_BIND_HOST = "0.0.0.0"
    else:
        ACTIVE_BIND_HOST = "127.0.0.1"
    # Local server restart reconciliation (build .61): if the
    # previous bridge recorded a restart request before exiting,
    # this bridge is its answer — verify this process's actual bind
    # against the saved choice and record the verdict where the
    # Settings row reads it. A match confirms; a mismatch fails at
    # the verify step and names the state that is actually live.
    _ps = public_settings(cfg)
    if _ps["restart_status"] == "restarting":
        if _ps["enabled"] == (ACTIVE_BIND_HOST == "0.0.0.0"):
            set_public_restart(cfg, "confirmed", "", "Restart complete — the bridge that answers now reports " + ("Local — on your network." if _ps["enabled"] else "This machine only."))
        else:
            set_public_restart(cfg, "failed", "verify", "A bridge answered after the restart, but its bind does not match the saved choice, so the change is not confirmed. Still live: " + ("Local — on your network (the old setting)." if ACTIVE_BIND_HOST == "0.0.0.0" else "This machine only — 127.0.0.1 (the old setting).") + " Press Restart bridge in Settings to try again, or quit Apex fully and relaunch.")
    # Threading: a connect that starts the server can wait minutes
    # for the model to load; it must not block status and chat.
    server = None
    deadline = time.time() + 30
    while server is None:
        try:
            server = ThreadingHTTPServer((ACTIVE_BIND_HOST, port), Handler)
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
                    # Name the holder by PID when the socket itself
                    # can resolve it (build .91): "end the python
                    # bridge.py process" sent the operator hunting
                    # through a process list for a process nothing
                    # would identify — the exact state a wedged
                    # update leaves behind.
                    _hp = port_holder_pid(port)
                    if _hp:
                        print("Port " + str(port) + " is still held by process "
                              + str(_hp) + " ("
                              + (pid_cmdline(_hp) or "unknown command")
                              + "), and it did not step aside. End it with: "
                              "kill -9 " + str(_hp)
                              + " — then launch Apex again.", flush=True)
                    else:
                        print("Port " + str(port) + " is still held by the older "
                              "bridge, and it did not step aside — it predates the "
                              "self-update watchdog. Quit the running Navi bridge "
                              "(close the app, or end the python bridge.py process) "
                              "and launch again.", flush=True)
                sys.exit(1)
            time.sleep(1)
    print("Navi bridge (build " + BRIDGE_BUILD + ") on http://localhost:" + str(port), flush=True)
    # Background update re-check (build .86): the bridge keeps its
    # own update verdict fresh while it runs (see _update_bg_loop).
    threading.Thread(target=_update_bg_loop, daemon=True).start()
    if ACTIVE_BIND_HOST == "0.0.0.0":
        print("Local server is ON: the dashboard also answers on the local network at "
              + public_state_payload(load_config(), True)["lanUrl"]
              + " - visitors from other machines need the access code from Settings.", flush=True)
    # DHD (build .74): if the saved choice is on, bring the public
    # door up now - certificate, proxy, self-check - and start the
    # daily renewal watch. A failed bring-up names itself in the
    # DHD state the dashboard reads; the bridge itself serves on.
    if dhd_settings(cfg)["enabled"]:
        threading.Thread(target=dhd_renewal_loop, daemon=True).start()
        if dhd_bring_up(load_config()):
            _dp = dhd_state_payload(load_config(), True)
            print("DHD is ON: " + _dhd_on_summary(_dp)
                  + " The proxy on 80/443 is the only public face; visitors need the access code.", flush=True)
        else:
            print("DHD is saved ON but did not come up: " + DHD_STATE["last_error"], flush=True)
        # If an enable operation was waiting on this restart, its
        # persisted card now reconciles with the live state.
        dhd_resume_enable_operation()
    # Navi Mesh (Ring 1; dedicated door since build .86): if Mesh
    # is on, open its dedicated TLS listener on the mesh port —
    # always, whether or not DHD is on. Mesh never rides the DHD
    # door; the proxy refuses /mesh/* outright.
    if mesh_settings(cfg)["enabled"]:
        mesh_start_listener()
        if MESH_SERVERS:
            print("Navi Mesh is ON: the dedicated Mesh door listens on port "
                  + str(mesh_settings(cfg)["port"]) + " (TLS, fingerprint-pinned).", flush=True)
        else:
            print("Navi Mesh is ON but its dedicated door did not open — see the Mesh page.", flush=True)
    server.serve_forever()
