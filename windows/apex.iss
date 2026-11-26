; Apex — Inno Setup script (Windows installer v1).
;
; This wrapper does exactly three things:
;   1. Lands the assembled package (payload + bundled Python
;      runtime + shell + the PowerShell machinery) in a
;      per-user package folder, {localappdata}\Navi-Apex-Package.
;      No admin, ever (PrivilegesRequired=lowest).
;   2. Ensures the WebView2 runtime the Tauri shell needs
;      (fetched from Microsoft if absent — the Rockport client
;      precedent). If it cannot be fetched, setup says so and
;      Apex simply opens in the default browser instead.
;   3. Runs windows\install.ps1, which performs the actual
;      placement into {localappdata}\Navi-Apex under the five
;      laws (manifest verify, stage-and-swap, keep-list,
;      llamafile pin, logon task, self-check with rollback).
;      Inno never places payload files into the install home
;      itself — placement is the installer's one act, not the
;      wrapper's.
;
; Unsigned (v1 ruling): SmartScreen's "More info -> Run
; anyway" is the accepted toll.
;
; Uninstall removes this package folder and the Navi-Apex
; logon task. It deliberately does NOT delete the install
; home ({localappdata}\Navi-Apex): that tree holds the
; operator's Soul/Memory, Mesh identity and chats, and an
; uninstaller has no business eating state. Delete the
; folder by hand if you want her gone entirely.
;
; Build (CI does this; see .github/workflows/windows-installer.yml):
;   ISCC /DSrcDir=<assembled dist> /DAppVersion=0.8.6e windows\apex.iss

#ifndef SrcDir
  #define SrcDir "dist"
#endif
#ifndef AppVersion
  #define AppVersion "0.8.6e"
#endif

[Setup]
AppId={{B7E3A1C4-2D5F-4A6B-8C7D-1E2F3A4B5C6D}
AppName=Apex
AppVerName=Apex {#AppVersion}
AppPublisher=SaintsSec
AppPublisherURL=https://nocturnerow.com/apex.html
DefaultDirName={localappdata}\Navi-Apex-Package
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=apex-{#AppVersion}-windows-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#SrcDir}\assets\navi-apex.ico
UninstallDisplayIcon={localappdata}\Navi-Apex\assets\navi-apex.ico

[Files]
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{userprograms}\Apex"; Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{localappdata}\Navi-Apex\start-apex.ps1"""; \
  WorkingDir: "{localappdata}\Navi-Apex"; \
  IconFilename: "{localappdata}\Navi-Apex\assets\navi-apex.ico"; \
  Comment: "Apex — Powered by Navi"

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""Navi-Apex"" /F"; \
  Flags: runhidden; RunOnceId: "DeleteLogonTask"

[Code]
function WebView2Installed: Boolean;
var
  Version: String;
begin
  { The WebView2 Runtime registers under this EdgeUpdate
    client GUID, machine-wide (HKLM, incl. the WOW6432 view)
    or per-user (HKCU). }
  Result :=
    (RegQueryStringValue(HKLM,
      'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU,
      'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
end;

procedure EnsureWebView2;
var
  ResultCode: Integer;
  Bootstrapper: String;
begin
  if WebView2Installed then
    Exit;
  Bootstrapper := ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe');
  try
    DownloadTemporaryFile(
      'https://go.microsoft.com/fwlink/p/?LinkId=2124703',
      'MicrosoftEdgeWebview2Setup.exe', '', nil);
  except
    MsgBox('The WebView2 runtime (needed for Apex''s own window) could not ' +
           'be downloaded. Apex will open in your default browser instead — ' +
           'everything else works the same.', mbInformation, MB_OK);
    Exit;
  end;
  if not Exec(Bootstrapper, '/silent /install', '', SW_SHOW,
              ewWaitUntilTerminated, ResultCode) then
    MsgBox('The WebView2 runtime installer could not be run. Apex will ' +
           'open in your default browser instead.', mbInformation, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Args: String;
begin
  if CurStep <> ssPostInstall then
    Exit;
  EnsureWebView2;
  { Placement is install.ps1's act (the five laws). Its own
    console stays visible: the operator watches the manifest
    verify, the model download and the self-check happen. }
  Args := '-NoProfile -ExecutionPolicy Bypass -File "' +
          ExpandConstant('{app}\windows\install.ps1') + '"';
  if not Exec('powershell.exe', Args, ExpandConstant('{app}'),
              SW_SHOW, ewWaitUntilTerminated, ResultCode) then
    ResultCode := -1;
  if ResultCode <> 0 then
    MsgBox('Apex placement did not complete — the installer window ' +
           'above names the reason, and nothing was half-placed: the ' +
           'previous version (if any) still stands whole. Setup will ' +
           'finish, but Apex is NOT installed until install.ps1 runs ' +
           'clean. You can re-run it at any time: ' +
           ExpandConstant('{app}\windows\install.ps1') + '.', mbError, MB_OK);
end;
