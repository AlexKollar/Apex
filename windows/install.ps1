# Apex — Windows installer (v1, the windows-installer build).
#
# The five laws from install.sh, in PowerShell dress. The laws
# are the contract; only the clothes are platform-shaped:
#
#   A) The payload is a CONTRACT. MANIFEST.txt declares every
#      file this package carries, its class and its sha256.
#      This installer copies and verifies FROM the manifest —
#      there are no hand-written per-file copy lists.
#   B) Placement is ONE ACT. The new tree is assembled in a
#      staging directory BESIDE the live tree and promoted by
#      rename; a kill or failure at any point leaves the
#      previous version ENTIRELY live or the new version
#      entirely live — never a mixture.
#   C) Provisioning is not placement. Everything here is
#      per-user and admin-free; run under an elevated token
#      this installer REFUSES up front, by name, before
#      anything is touched (an elevated placement would land
#      files owned by the wrong context and register the
#      logon task against the wrong identity).
#   D) Permissions are audited, not discovered. Before
#      anything is stopped or carried, the existing tree is
#      audited in ONE pass for state this operator cannot
#      read; irreplaceable state (Mesh identity, cards,
#      chats, Case Files, Soul/Memory, config) refuses the
#      install up front, naming EVERY offender.
#   E) The incoming build governs its own installation —
#      NAMED GAP for Windows v1: the in-app updater's pull
#      machinery stays Linux-only, so on Windows the update
#      path is re-running the newest installer. That is safe
#      by construction here: a re-run is the same stage-and-
#      swap, with the same keep-list, as a first install.
#
# What an install preserves, untouched as ever: the llamafile,
# installed chips and RAG packs, the Vault, DHD certificates,
# the Mesh identity, chats, config, and the operator's
# Soul/Memory. -Fresh still means a clean payload over the
# same keep-list. (The voice venv is a named v1 gap: it is
# carried if present, never built here.)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Fresh
#   powershell -ExecutionPolicy Bypass -File install.ps1 -InstallDir D:\Apex
#
[CmdletBinding()]
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'Navi-Apex'),
    [switch]$Fresh,
    [switch]$NoTask
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# When Inno Setup drives this script the payload sits beside it;
# in the repo / zip layout the payload is the tree above windows/.
if (-not (Test-Path (Join-Path $SrcDir 'MANIFEST.txt'))) {
    $SrcDir = Split-Path -Parent $SrcDir
}

$LlamafileUrl = 'https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile'
# Llamafile integrity pin (#184): the sha256 of the navi.llamafile
# this installer will accept — the same pin install.sh carries,
# read from Hugging Face's own X-Linked-ETag for
# saintssec/navi.llamafile.
$LlamafileSha256 = 'd2d0858c7be2567b8d54d01ae606a62be4aae9f46447bd0450f4df141d0dbcd6'
$BridgePort = 8675

function Say($text) { Write-Host "==> $text" }
function Note($text) { Write-Host "    $text" }
function Refuse($text) {
    Write-Host "ERROR: $text" -ForegroundColor Red
    exit 1
}

# --- Law C: never under an elevated token ----------------------
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Refuse ("this installer is running with an elevated (administrator) token. " +
            "Apex installs per-user into $InstallDir and registers its logon " +
            "task against YOUR identity — an elevated run would land both " +
            "against the wrong one. Close this window and re-run install.ps1 " +
            "from an ordinary, non-elevated PowerShell.")
}

if (-not (Test-Path (Join-Path $SrcDir 'MANIFEST.txt'))) {
    Refuse "MANIFEST.txt not found beside the installer (looked in $SrcDir) — this package is incomplete."
}
if (-not (Test-Path (Join-Path $SrcDir 'runtime\python.exe'))) {
    Refuse ("the bundled Python runtime is missing (runtime\python.exe) — " +
            "this package is incomplete. The Windows package carries its own " +
            "interpreter; it never borrows a system Python.")
}
$Python = Join-Path $SrcDir 'runtime\python.exe'

# --- The manifest (Law A) --------------------------------------
function Read-Manifest {
    $rows = @()
    foreach ($line in Get-Content (Join-Path $SrcDir 'MANIFEST.txt')) {
        if (-not $line -or $line.StartsWith('#')) { continue }
        $parts = $line -split "`t", 3
        if ($parts.Count -lt 3) { continue }
        $rows += [pscustomobject]@{ Path = $parts[0]; Class = $parts[1]; Sha256 = $parts[2] }
    }
    return $rows
}
$Manifest = Read-Manifest

function Get-Sha256($path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
}

# Verify the package itself against the manifest before a byte
# is placed: a truncated or tampered download refuses here,
# with the live tree untouched.
Say 'Verifying the package against its manifest (Law A)'
foreach ($row in $Manifest) {
    if ($row.Class -eq 'package-only') { continue }
    if ($row.Sha256 -eq '-') { continue }
    $p = Join-Path $SrcDir ($row.Path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p)) {
        Refuse "the package is missing $($row.Path) (named in MANIFEST.txt) — the download is incomplete."
    }
    if ((Get-Sha256 $p) -ne $row.Sha256) {
        Refuse "integrity failure: $($row.Path) does not match its MANIFEST.txt sha256 — the download is truncated or tampered. Nothing was installed."
    }
}
Note 'package verified'

# --- Law D: audit the existing tree before anything moves -----
$IsUpdate = Test-Path (Join-Path $InstallDir 'bridge.py')
if ($IsUpdate) {
    Say 'Auditing the existing install before anything is touched (Law D)'
    $offenders = @()
    # Irreplaceable state: config (Soul/Memory, Mesh identity,
    # chats, Vault, DHD certs ride inside it), chips, packs.
    $auditRoots = @('config', 'chips', 'rag-packs')
    foreach ($rel in $auditRoots) {
        $root = Join-Path $InstallDir $rel
        if (-not (Test-Path $root)) { continue }
        foreach ($f in Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue) {
            try {
                $s = [System.IO.File]::Open($f.FullName, 'Open', 'Read', 'ReadWrite')
                $s.Close()
            } catch {
                $offenders += $f.FullName.Substring($InstallDir.Length + 1)
            }
        }
    }
    if ($offenders.Count -gt 0) {
        Write-Host 'ERROR: the install is refused before anything is stopped or carried.' -ForegroundColor Red
        Write-Host '       These irreplaceable files cannot be read by this operator:' -ForegroundColor Red
        foreach ($o in $offenders) { Write-Host "         - $o" -ForegroundColor Red }
        Write-Host '       Remedy: close whatever holds them (an editor, a sync client), or fix their' -ForegroundColor Red
        Write-Host '       permissions so your own account can read them, then re-run the installer.' -ForegroundColor Red
        exit 1
    }
    Note 'audit clean — every irreplaceable file is readable'
}

# --- Stop the running build (by proven pid, never by name) -----
function Stop-ApexProcesses($dir) {
    $pidFile = Join-Path $dir 'bridge.pid'
    if (Test-Path $pidFile) {
        $bridgePid = 0
        if ([int]::TryParse((Get-Content $pidFile -Raw).Trim(), [ref]$bridgePid)) {
            $proc = Get-Process -Id $bridgePid -ErrorAction SilentlyContinue
            if ($proc) {
                Note "stopping the running bridge (pid $bridgePid, from bridge.pid)"
                Stop-Process -Id $bridgePid -Force -ErrorAction SilentlyContinue
                $proc.WaitForExit(10000) | Out-Null
            }
        }
    }
    # The engine: matched on its executable living in THIS tree,
    # never on a bare process name.
    $enginePath = Join-Path $dir 'navi.llamafile.exe'
    foreach ($proc in Get-Process -ErrorAction SilentlyContinue) {
        try {
            if ($proc.Path -and $proc.Path -eq $enginePath) {
                Note "stopping the running engine (pid $($proc.Id))"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $proc.WaitForExit(10000) | Out-Null
            }
        } catch { }
    }
}
if ($IsUpdate) { Stop-ApexProcesses $InstallDir }

# --- Stage assembly (Law B) ------------------------------------
$ParentDir = Split-Path -Parent $InstallDir
New-Item -ItemType Directory -Force -Path $ParentDir | Out-Null
$StageDir = "$InstallDir.stage"
$ParkDir = "$InstallDir.previous"
if (Test-Path $StageDir) { Remove-Item -LiteralPath $StageDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

function Copy-Tree($from, $to) {
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Get-ChildItem -LiteralPath $from -Recurse -Force | ForEach-Object {
        $rel = $_.FullName.Substring($from.Length + 1)
        if ($rel -match '(^|\\)__pycache__(\\|$)' -or $_.Name -like '*.pyc') { return }
        $dest = Join-Path $to $rel
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
        }
    }
}

if ($IsUpdate -and -not $Fresh) {
    # The whole previous tree is the stage's foundation —
    # operator state and all — minus regenerable bytecode and
    # minus update staging. Payload files overwrite it from
    # the manifest below.
    Say 'Assembling the new tree beside the live one (foundation: the current install)'
    Copy-Tree $InstallDir $StageDir
    $upd = Join-Path $StageDir 'updates'
    if (Test-Path $upd) { Remove-Item -LiteralPath $upd -Recurse -Force }
} elseif ($IsUpdate -and $Fresh) {
    Say 'Assembling the new tree beside the live one (fresh payload, standing keep-list)'
    foreach ($d in @('chips', 'rag-packs')) {
        $s = Join-Path $InstallDir $d
        if (Test-Path $s) { Copy-Tree $s (Join-Path $StageDir $d) }
    }
    $cfgSrc = Join-Path $InstallDir 'config'
    if (Test-Path $cfgSrc) {
        foreach ($d in @('vault', 'dhd', 'mesh', 'chats')) {
            $s = Join-Path $cfgSrc $d
            if (Test-Path $s) { Copy-Tree $s (Join-Path (Join-Path $StageDir 'config') $d) }
        }
        foreach ($f in @('navi.config.json', 'soul.md', 'memory.md')) {
            $s = Join-Path $cfgSrc $f
            if (Test-Path $s) {
                New-Item -ItemType Directory -Force -Path (Join-Path $StageDir 'config') | Out-Null
                Copy-Item -LiteralPath $s -Destination (Join-Path (Join-Path $StageDir 'config') $f) -Force
            }
        }
    }
    $llama = Join-Path $InstallDir 'navi.llamafile.exe'
    if (Test-Path $llama) { Copy-Item -LiteralPath $llama -Destination (Join-Path $StageDir 'navi.llamafile.exe') -Force }
    $llamaPlain = Join-Path $InstallDir 'navi.llamafile'
    if (-not (Test-Path (Join-Path $StageDir 'navi.llamafile.exe')) -and (Test-Path $llamaPlain)) {
        Copy-Item -LiteralPath $llamaPlain -Destination (Join-Path $StageDir 'navi.llamafile.exe') -Force
    }
    foreach ($d in @('models', 'venv')) {
        $s = Join-Path (Join-Path $InstallDir 'voice') $d
        if (Test-Path $s) { Copy-Tree $s (Join-Path (Join-Path $StageDir 'voice') $d) }
    }
    $calls = Join-Path (Join-Path $InstallDir 'voice') 'calls.json'
    if (Test-Path $calls) {
        New-Item -ItemType Directory -Force -Path (Join-Path $StageDir 'voice') | Out-Null
        Copy-Item -LiteralPath $calls -Destination (Join-Path (Join-Path $StageDir 'voice') 'calls.json') -Force
    }
} else {
    Say 'Assembling the new tree beside the live one (first install)'
    # A target holding ONLY a pre-seeded llamafile (the operator
    # fetched the binary themselves) keeps it — no download.
    $llamaPlain = Join-Path $InstallDir 'navi.llamafile'
    $llamaExe = Join-Path $InstallDir 'navi.llamafile.exe'
    if (Test-Path $llamaExe) {
        Copy-Item -LiteralPath $llamaExe -Destination (Join-Path $StageDir 'navi.llamafile.exe') -Force
        Note 'navi.llamafile already present at the target — keeping it (no download)'
    } elseif (Test-Path $llamaPlain) {
        Copy-Item -LiteralPath $llamaPlain -Destination (Join-Path $StageDir 'navi.llamafile.exe') -Force
        Note 'navi.llamafile already present at the target — keeping it (no download)'
    }
}

# The payload, FROM the manifest: every payload file lands;
# every seed-config file lands only where the tree has none;
# generated files are produced below; package-only never lands.
foreach ($row in $Manifest) {
    $rel = $row.Path -replace '/', '\'
    $dest = Join-Path $StageDir $rel
    switch ($row.Class) {
        'payload' {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
            Copy-Item -LiteralPath (Join-Path $SrcDir $rel) -Destination $dest -Force
        }
        'seed-config' {
            if (-not (Test-Path $dest)) {
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
                Copy-Item -LiteralPath (Join-Path $SrcDir $rel) -Destination $dest -Force
            }
        }
    }
}
Note 'payload placed from the manifest'

# The bundled runtime and the Windows machinery land beside
# the payload (they are package furniture, not manifest rows:
# the manifest is the cross-platform payload contract).
Copy-Tree (Join-Path $SrcDir 'runtime') (Join-Path $StageDir 'runtime')
foreach ($f in @('install.ps1', 'start-apex.ps1')) {
    $s = Join-Path $SrcDir "windows\$f"
    if (-not (Test-Path $s)) { $s = Join-Path $SrcDir $f }
    Copy-Item -LiteralPath $s -Destination (Join-Path $StageDir $f) -Force
}
$shellExe = Join-Path $SrcDir 'navi-apex-shell.exe'
if (Test-Path $shellExe) {
    Copy-Item -LiteralPath $shellExe -Destination (Join-Path $StageDir 'navi-apex-shell.exe') -Force
    Note 'the Tauri shell is in the tree — she gets her own window'
} else {
    Note 'no shell binary in this package — the dashboard opens in the default browser'
}

# Standing homes the bridge expects, present from the first run.
foreach ($d in @('config\dhd', 'config\mesh', 'config\chats', 'voice\models')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $StageDir $d) | Out-Null
}

# The model file: carried across above when one exists; a first
# install downloads it into the STAGE — a failed download
# aborts here, with the live tree (if any) entirely untouched.
$stageLlama = Join-Path $StageDir 'navi.llamafile.exe'
if (Test-Path $stageLlama) {
    $fs = [System.IO.File]::OpenRead($stageLlama)
    try {
        $buf = New-Object byte[] 15
        $n = $fs.Read($buf, 0, 15)
        $headText = [System.Text.Encoding]::ASCII.GetString($buf, 0, $n)
    } finally { $fs.Close() }
    if ($headText -match '<!DOCTYPE|<html') {
        Remove-Item -LiteralPath $stageLlama -Force
    }
}
if (-not (Test-Path $stageLlama)) {
    Say 'Downloading the Navi llamafile'
    Note "from: $LlamafileUrl"
    Note "pinned sha256 (#184): $LlamafileSha256"
    $tmp = "$stageLlama.download"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $wc = New-Object Net.WebClient
        $wc.DownloadFile($LlamafileUrl, $tmp)
    } catch {
        Refuse "the model download failed ($($_.Exception.Message)) — aborting with the live tree untouched. The staged tree is left at $StageDir for inspection."
    }
    if ((Get-Sha256 $tmp) -ne $LlamafileSha256) {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        Refuse ("LLAMAFILE INTEGRITY FAILURE (#184): the downloaded navi.llamafile does not match the " +
                "pinned sha256. This is a hard stop, not a warning — a tampered or truncated model " +
                "binary does not land on this machine. Nothing was installed.")
    }
    Move-Item -LiteralPath $tmp -Destination $stageLlama -Force
    Note 'llamafile verified against the pinned sha256 (#184) — in place, as navi.llamafile.exe'
}

# Record this install in the config: the startup choice, the
# bridge's host/port, and the install directory — the same
# fields install.sh stamps. The operator's own settings and
# any manual hardware override stay untouched (the bridge
# profiles this machine itself on first start).
$cfgPath = Join-Path $StageDir 'config\navi.config.json'
& $Python -c @"
import json, sys
path, install_dir, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
with open(path) as f:
    cfg = json.load(f)
cfg['startup'] = 'on-boot'
cfg['headless'] = False
cfg.setdefault('bridge', {})['host'] = '127.0.0.1'
cfg['bridge']['port'] = port
cfg['install_dir'] = install_dir
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
"@ $cfgPath $InstallDir $BridgePort
if ($LASTEXITCODE -ne 0) { Refuse 'the install record could not be written into the config — aborting with the live tree untouched.' }

# --- The swap (Law B's second half) -----------------------------
Say 'Placing the new tree (one act: rename, never a mixture)'
if (Test-Path $ParkDir) { Remove-Item -LiteralPath $ParkDir -Recurse -Force }
if (Test-Path $InstallDir) {
    Rename-Item -LiteralPath $InstallDir -NewName (Split-Path -Leaf $ParkDir)
}
try {
    Rename-Item -LiteralPath $StageDir -NewName (Split-Path -Leaf $InstallDir)
} catch {
    # Roll the previous tree straight back — the install stands
    # or falls as one act.
    if (Test-Path $ParkDir) { Rename-Item -LiteralPath $ParkDir -NewName (Split-Path -Leaf $InstallDir) }
    Refuse "the placement rename failed ($($_.Exception.Message)) — the previous version was restored whole."
}

# --- Self-verification, with rollback on a failed verdict -------
Say 'Verifying the placed tree (the install stands or rolls back on this verdict)'
$verifyFailed = $null
foreach ($row in $Manifest) {
    if ($row.Class -ne 'payload' -or $row.Sha256 -eq '-') { continue }
    $p = Join-Path $InstallDir ($row.Path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p)) { $verifyFailed = "missing after placement: $($row.Path)"; break }
    if ((Get-Sha256 $p) -ne $row.Sha256) { $verifyFailed = "hash mismatch after placement: $($row.Path)"; break }
}
if (-not $verifyFailed) {
    & (Join-Path $InstallDir 'runtime\python.exe') (Join-Path $InstallDir 'bridge.py') --self-check | Out-Null
    if ($LASTEXITCODE -ne 0) { $verifyFailed = 'bridge.py --self-check returned a failed verdict' }
}
if ($verifyFailed) {
    Write-Host "ERROR: self-verification failed ($verifyFailed) — rolling back." -ForegroundColor Red
    Stop-ApexProcesses $InstallDir
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
    if (Test-Path $ParkDir) {
        Rename-Item -LiteralPath $ParkDir -NewName (Split-Path -Leaf $InstallDir)
        Write-Host '    the previous version was restored whole.' -ForegroundColor Red
    }
    exit 1
}
Note 'placed tree verified — manifest hashes and the bridge self-check agree'

# --- The logon task (the Windows mirror of the user units) ------
if (-not $NoTask) {
    Say 'Registering the per-user logon task'
    $launcher = Join-Path $InstallDir 'start-apex.ps1'
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`" -Headless"
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName 'Navi-Apex' -Action $action -Trigger $trigger `
        -Settings $settings -Description 'Apex (Powered by Navi) — engine and bridge, started at logon.' -Force | Out-Null
    Note "task 'Navi-Apex' registered for $($identity.Name) — per-user, no elevation"
}

# The parked previous tree is the rollback point; the record of
# this install lands beside the config, as it does on Linux.
$record = [ordered]@{
    installedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    version = (Get-Content (Join-Path $InstallDir 'VERSION') -Raw).Trim()
    installDir = $InstallDir
    fresh = [bool]$Fresh
    platform = 'windows'
}
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $InstallDir 'config\install-record.json') -Encoding UTF8

if (Test-Path $ParkDir) {
    Note "the previous version is parked at $ParkDir — re-running its installer, or renaming it back, is the rollback"
}
Say 'Apex is installed.'
Note "home: $InstallDir"
Note 'start her from the Start Menu (Apex), or run start-apex.ps1 in the install home.'
Note 'she also starts herself at logon (task: Navi-Apex).'
