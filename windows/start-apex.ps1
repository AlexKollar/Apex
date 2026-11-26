# Apex — Windows launcher (v1, the windows-installer build).
#
# start.sh's flow, in PowerShell dress:
#   1. The engine: navi.llamafile.exe --server --v2 plus the
#      runtime flags from config/navi.config.json — the exact
#      derivation run-llamafile.sh performs (runtime block
#      first, then the hardware profile's settings, then the
#      fluid floor: ctx 4096 / 4 threads / batch 512).
#      Check-first: a port already answering is adopted, and
#      an owner mid-start (process alive, model still loading)
#      is waited for, never raced.
#   2. The bridge: the bundled runtime's python (the voice
#      venv's python when a venv exists, as on Linux),
#      check-first against /api/status naming "Navi: Apex".
#   3. The front door: her own Tauri window when the shell
#      binary is in the tree, the default browser otherwise.
#      -Headless starts the services only — it is the mode
#      the Navi-Apex logon task runs.
#
# Everything this launcher decides lands in start.log beside
# the app: a Start Menu or logon launch has no terminal, and
# a window that failed to open must not fail in silence.
#
# One Linux behaviour is deliberately NOT mirrored in v1:
# start.sh's supervise loop (restart the bridge when it exits
# with code 75 — "replaced"). On Windows the updater is the
# installer (see install.ps1, Law E), and the installer stops
# and restarts her itself; a dead bridge here stays down
# until the next launch or logon, and says so in start.log.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File start-apex.ps1
#   powershell -ExecutionPolicy Bypass -File start-apex.ps1 -Headless
#
[CmdletBinding()]
param([switch]$Headless)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$LogFile = Join-Path $Root 'start.log'
$EnginePort = if ($env:NAVI_LLAMAFILE_PORT) { [int]$env:NAVI_LLAMAFILE_PORT } else { 8080 }
$BridgePort = if ($env:NAVI_BRIDGE_PORT) { [int]$env:NAVI_BRIDGE_PORT } else { 8675 }

function Log($text) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $text
    Add-Content -LiteralPath $LogFile -Value $line -ErrorAction SilentlyContinue
    Write-Host $text
}

function Test-PortAnswering($port) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$port/" -TimeoutSec 2 -UseBasicParsing
        return $r.StatusCode -ge 200
    } catch {
        # A non-2xx answer is still an answer — something is
        # listening and speaking HTTP.
        if ($_.Exception.Response) { return $true }
        return $false
    }
}

function Test-BridgeAnswering {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$BridgePort/api/status" -TimeoutSec 2 -UseBasicParsing
        return ($r.Content -match '"app"\s*:\s*"Navi: Apex"')
    } catch { return $false }
}

Log "launch: Apex starting (llamafile port $EnginePort, bridge port $BridgePort)"
if ($Headless) { Log 'launch mode: headless — services only, no window' }

# --- The engine -------------------------------------------------
$Python = Join-Path $Root 'runtime\python.exe'
$Engine = Join-Path $Root 'navi.llamafile.exe'
if (-not (Test-Path $Engine)) { $Engine = Join-Path $Root 'navi.llamafile' }

# The flag derivation, byte-for-byte run-llamafile.sh's logic.
$flags = & $Python -c @"
import json
try:
    with open('config/navi.config.json') as f:
        cfg = json.load(f)
    rt = cfg.get('runtime') or {}
    hp = (cfg.get('hardware_profile') or {}).get('settings') or {}
    ctx = int(rt.get('ctx_size') or hp.get('ctxSize') or 4096)
    thr = int(rt.get('threads') or hp.get('threads') or 4)
    bat = int(rt.get('batch_size') or hp.get('batchSize') or 512)
    gpu = int(rt.get('gpu_layers') if rt.get('gpu_layers') is not None else (hp.get('gpuLayers') or 0))
    out = '--ctx-size %d --threads %d --batch-size %d' % (ctx, thr, bat)
    if gpu > 0:
        out += ' --n-gpu-layers %d' % gpu
    print(out)
except Exception:
    print('--ctx-size 4096 --threads 4 --batch-size 512')
"@
if (-not $flags) { $flags = '--ctx-size 4096 --threads 4 --batch-size 512' }
$flagList = $flags -split ' '

if (Test-PortAnswering $EnginePort) {
    Log "llamafile: already answering on port $EnginePort — adopting it, not spawning"
} else {
    $owner = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try { $_.Path -and ($_.Path -eq $Engine) } catch { $false }
    }
    if ($owner) {
        Log 'llamafile: another owner is starting her — waiting for the port, not spawning'
        $deadline = (Get-Date).AddSeconds(120)
        $up = $false
        while ((Get-Date) -lt $deadline) {
            if (Test-PortAnswering $EnginePort) { $up = $true; break }
            Start-Sleep -Seconds 2
        }
        if (-not $up) {
            Log 'llamafile: another owner is still starting her after two minutes — not spawning; the bridge can retry the start from the UI (Connect).'
        }
    } elseif (-not (Test-Path $Engine)) {
        Log "llamafile: no engine binary in $Root — run the installer so it can download the model server."
    } else {
        Log "llamafile: starting ($flags)"
        $engineArgs = @('--server', '--v2', '--port', "$EnginePort") + $flagList
        Start-Process -FilePath $Engine -ArgumentList $engineArgs -WorkingDirectory $Root `
            -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root 'navi.llamafile.log') `
            -RedirectStandardError (Join-Path $Root 'navi.llamafile.err.log') | Out-Null
        $deadline = (Get-Date).AddSeconds(120)
        $up = $false
        while ((Get-Date) -lt $deadline) {
            if (Test-PortAnswering $EnginePort) { $up = $true; break }
            Start-Sleep -Seconds 2
        }
        if ($up) { Log "llamafile: answering on port $EnginePort" }
        else { Log 'llamafile: not answering after two minutes — its output is in navi.llamafile.log beside the app.' }
    }
}

# --- The bridge ---------------------------------------------------
$BridgePython = $Python
$venvPython = Join-Path $Root 'voice\venv\Scripts\python.exe'
if (Test-Path $venvPython) { $BridgePython = $venvPython }

if (Test-BridgeAnswering) {
    Log "bridge: already answering on port $BridgePort — adopted, not doubled"
} else {
    Log "bridge: starting the bridge on port $BridgePort"
    Start-Process -FilePath $BridgePython -ArgumentList 'bridge.py' -WorkingDirectory $Root `
        -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root 'bridge.out.log') `
        -RedirectStandardError (Join-Path $Root 'bridge.err.log') | Out-Null
    $deadline = (Get-Date).AddSeconds(60)
    $up = $false
    while ((Get-Date) -lt $deadline) {
        if (Test-BridgeAnswering) { $up = $true; break }
        Start-Sleep -Seconds 2
    }
    if ($up) { Log "bridge: verified answering on port $BridgePort" }
    else { Log 'bridge: not answering after a minute — its output is in bridge.err.log beside the app.' }
}

# --- The front door ------------------------------------------------
if ($Headless) {
    Log 'headless: services started — no window opened'
    return
}
$Shell = Join-Path $Root 'navi-apex-shell.exe'
if (Test-Path $Shell) {
    Log 'front door: her own window (the Tauri shell)'
    Start-Process -FilePath $Shell -WorkingDirectory $Root | Out-Null
} else {
    Log 'front door: no shell binary in the tree — the dashboard opens in the default browser'
    Start-Process "http://localhost:$BridgePort/" | Out-Null
}
