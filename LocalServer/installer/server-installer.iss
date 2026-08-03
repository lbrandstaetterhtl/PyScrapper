; ============================================================
;  PyScrapper Server - Standalone Installer (Inno Setup)
;  Nur der FastAPI-Server (LocalServer + PythonModule)
;  Embedded Python 3.12 + ffmpeg + Playwright + yt-dlp
;  Manueller Start per start-server.bat
;  Kompilieren: Inno Setup oeffnen -> F9   |   ISCC.exe server-installer.iss
; ============================================================

#define MyAppName        "PyScrapper Server"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Leon Brandstetter"

; ---- WICHTIG: Pfad zu deinem Projekt-Root anpassen ----
#define ProjectRoot      "C:\Users\p50232\RiderProjects\PyScrapper"

[Setup]
AppId={{B8F5A3D0-4C2E-4F9B-A07D-3E6C9B2F1D85}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}

PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\PyScrapperServer
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}

Compression=none
SolidCompression=no
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputBaseFilename=PyScrapper-Server-Setup-{#MyAppVersion}
OutputDir=installer-output

UninstallDisplayName={#MyAppName}
CloseApplications=no

WizardSizePercent=120

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Files]
; --- Server-Code (LocalServer) ---
; .env und .venv werden ausgeschlossen - .env wird frisch generiert (siehe [Code])
Source: "{#ProjectRoot}\LocalServer\*"; DestDir: "{app}\LocalServer"; \
    Excludes: ".venv,__pycache__,*.pyc,.env,logs\*,Data\*.db"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; --- PythonModule (MUSS Geschwister von LocalServer sein, wegen sys.path.insert in server.py) ---
Source: "{#ProjectRoot}\PythonModule\*"; DestDir: "{app}\PythonModule"; \
    Excludes: "__pycache__,*.pyc"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; --- requirements.txt (liegt im LocalServer-Ordner) ---
; Bereits durch LocalServer\* mit abgedeckt, aber explizit sicherstellen:
; Source: "{#ProjectRoot}\LocalServer\requirements.txt"; DestDir: "{app}\LocalServer"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\data"
Name: "{app}\LocalServer\logs"
Name: "{app}\LocalServer\Data"
Name: "{app}\ffmpeg"

[Icons]
Name: "{group}\PyScrapper Server starten"; Filename: "{app}\start-server.bat"
Name: "{group}\{#MyAppName} deinstallieren"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\start-server.bat"; Description: "Server jetzt starten"; Flags: postinstall skipifsilent shellexec nowait

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\LocalServer\__pycache__"
Type: filesandordirs; Name: "{app}\PythonModule\__pycache__"
Type: dirifempty; Name: "{app}\logs"
Type: dirifempty; Name: "{app}\data"
Type: dirifempty; Name: "{app}\ffmpeg"

; ============================================================
;  Code: Download + Live-Installation mit Fortschritt & Log
; ============================================================
[Code]
function SendMessage(hWnd: Integer; Msg: Integer; wParam: Integer; lParam: Integer): Integer;
  external 'SendMessageW@user32.dll stdcall';

const
  EM_SCROLLCARET = $00B7;
  STEP_COUNT     = 6;

  VCREDIST_URL = 'https://aka.ms/vs/17/release/vc_redist.x64.exe';
  PYTHON_URL   = 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip';
  GETPIP_URL   = 'https://bootstrap.pypa.io/get-pip.py';
  FFMPEG_URL   = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip';

var
  DownloadPage: TDownloadWizardPage;
  LogMemo: TNewMemo;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(
    'Komponenten herunterladen',
    'Benoetigte Dateien werden heruntergeladen...',
    @OnDownloadProgress);

  LogMemo := TNewMemo.Create(WizardForm);
  LogMemo.Parent := WizardForm.InstallingPage;
  LogMemo.Left := WizardForm.ProgressGauge.Left;
  LogMemo.Top := WizardForm.ProgressGauge.Top + WizardForm.ProgressGauge.Height + ScaleY(12);
  LogMemo.Width := WizardForm.ProgressGauge.Width;
  LogMemo.Height := ScaleY(170);
  LogMemo.ReadOnly := True;
  LogMemo.ScrollBars := ssVertical;
  LogMemo.WordWrap := False;
  LogMemo.Font.Name := 'Consolas';
  LogMemo.Font.Size := 8;
  LogMemo.Color := $001E1E1E;
  LogMemo.Font.Color := $00D4D4D4;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpReady then
  begin
    DownloadPage.Clear;
    DownloadPage.Add(VCREDIST_URL, 'vc_redist.x64.exe',  '');
    DownloadPage.Add(PYTHON_URL,   'python-embed.zip',   '');
    DownloadPage.Add(GETPIP_URL,   'get-pip.py',         '');
    DownloadPage.Add(FFMPEG_URL,   'ffmpeg.zip',         '');
    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
      except
        SuppressibleMsgBox(AddPeriod(GetExceptionMessage), mbCriticalError, MB_OK, IDOK);
        Result := False;
      end;
    finally
      DownloadPage.Hide;
    end;
  end;
end;

procedure LogLine(const S: String);
begin
  LogMemo.Lines.Add(S);
  LogMemo.SelStart := Length(LogMemo.Text);
  SendMessage(LogMemo.Handle, EM_SCROLLCARET, 0, 0);
  LogMemo.Update;
end;

procedure SetStepProgress(StepIndex: Integer);
begin
  WizardForm.ProgressGauge.Position := Round(StepIndex / STEP_COUNT * 100);
  WizardForm.Update;
end;

procedure RunStreaming(const CmdLine, StepName: String; StepIndex: Integer);
var
  LogFile, DoneFile: String;
  ResultCode, LastLen, ExitCode: Integer;
  Whole, DoneTxt: AnsiString;
  FullCmd: String;
begin
  WizardForm.StatusLabel.Caption :=
    Format('Schritt %d von %d: %s', [StepIndex, STEP_COUNT, StepName]);
  LogLine('');
  LogLine('=== ' + StepName + ' ===');

  LogFile  := ExpandConstant('{tmp}\step.log');
  DoneFile := ExpandConstant('{tmp}\step.done');
  DeleteFile(LogFile);
  DeleteFile(DoneFile);

  FullCmd := '/V:ON /C (' + CmdLine + ') > "' + LogFile + '" 2>&1 & echo !ERRORLEVEL! > "' + DoneFile + '"';
  Exec(ExpandConstant('{cmd}'), FullCmd, '', SW_HIDE, ewNoWait, ResultCode);

  LastLen := 0;
  while not FileExists(DoneFile) do
  begin
    if LoadStringFromFile(LogFile, Whole) then
      if Length(Whole) > LastLen then
      begin
        LogMemo.Text := String(Whole);
        LogMemo.SelStart := Length(LogMemo.Text);
        SendMessage(LogMemo.Handle, EM_SCROLLCARET, 0, 0);
        LastLen := Length(Whole);
      end;
    WizardForm.Update;
    Sleep(200);
  end;

  if LoadStringFromFile(LogFile, Whole) then
  begin
    LogMemo.Text := String(Whole);
    LogMemo.SelStart := Length(LogMemo.Text);
    SendMessage(LogMemo.Handle, EM_SCROLLCARET, 0, 0);
  end;
  ExitCode := 0;
  if LoadStringFromFile(DoneFile, DoneTxt) then
    ExitCode := StrToIntDef(Trim(String(DoneTxt)), 0);
  if ExitCode <> 0 then
    LogLine('[Warnung] "' + StepName + '" endete mit Code ' + IntToStr(ExitCode));

  SetStepProgress(StepIndex);
end;

// Erzeugt einen zufaelligen ADMIN_KEY (32 Hex-Zeichen)
// Inno Setup hat kein Randomize. Wir seeden Random() ueber einen Zeit-String.
function GenerateAdminKey(): String;
var
  i, Seed, j: Integer;
  Chars, TimeStr: String;
begin
  // Seed aus aktuellem Zeit-String (HHNNSSZZZ) generieren
  TimeStr := GetDateTimeString('hhnnsszzz', #0, #0);
  Seed := 0;
  for j := 1 to Length(TimeStr) do
    Seed := Seed + (Ord(TimeStr[j]) * j);
  Random(Seed); // ersten Wert "verbrauchen" um die Sequenz zu variieren

  Chars := '0123456789abcdef';
  Result := '';
  for i := 1 to 32 do
    Result := Result + Chars[Random(16) + 1];
end;

// Schreibt die .env Datei mit generiertem ADMIN_KEY nach LocalServer\
procedure CreateEnvFile();
var
  EnvPath, AdminKey, Content: String;
begin
  AdminKey := GenerateAdminKey();
  EnvPath := ExpandConstant('{app}\LocalServer\.env');

  Content :=
    '# PyScrapper Server Konfiguration' + #13#10 +
    '# Automatisch generiert beim Setup - NICHT weitergeben!' + #13#10 +
    'ADMIN_KEY=' + AdminKey + #13#10;

  if SaveStringToFile(EnvPath, Content, False) then
  begin
    LogLine('.env erstellt mit generiertem ADMIN_KEY');
    LogLine('  -> ' + EnvPath);
  end
  else
    LogLine('[FEHLER] .env konnte nicht geschrieben werden!');
end;

// Schreibt start-server.bat nach {app}
procedure CreateStartScript();
var
  BatPath, Content: String;
begin
  BatPath := ExpandConstant('{app}\start-server.bat');

  Content :=
    '@echo off' + #13#10 +
    'REM PyScrapper Server Starter' + #13#10 +
    'setlocal' + #13#10 +
    '' + #13#10 +
    'set "APPDIR=%~dp0"' + #13#10 +
    'set "PYTHON=%APPDIR%python\python.exe"' + #13#10 +
    'set "SERVERDIR=%APPDIR%LocalServer"' + #13#10 +
    '' + #13#10 +
    'REM ffmpeg zum PATH hinzufuegen (fuer diese Session)' + #13#10 +
    'set "PATH=%APPDIR%ffmpeg;%PATH%"' + #13#10 +
    '' + #13#10 +
    'cls' + #13#10 +
    'echo ============================================' + #13#10 +
    'echo   PyScrapper Server' + #13#10 +
    'echo ============================================' + #13#10 +
    'echo.' + #13#10 +
    'echo   URL:    http://127.0.0.1:8765' + #13#10 +
    'echo   Docs:   http://127.0.0.1:8765/docs' + #13#10 +
    'echo   Health: http://127.0.0.1:8765/health' + #13#10 +
    'echo.' + #13#10 +
    'echo   Zum Beenden: Strg+C' + #13#10 +
    'echo ============================================' + #13#10 +
    'echo.' + #13#10 +
    '' + #13#10 +
    'cd /d "%SERVERDIR%"' + #13#10 +
    '"%PYTHON%" -m uvicorn server:app --host 127.0.0.1 --port 8765' + #13#10 +
    '' + #13#10 +
    'if errorlevel 1 (' + #13#10 +
    '    echo.' + #13#10 +
    '    echo Server wurde mit einem Fehler beendet.' + #13#10 +
    '    pause' + #13#10 +
    ')' + #13#10;

  if SaveStringToFile(BatPath, Content, False) then
    LogLine('start-server.bat erstellt')
  else
    LogLine('[FEHLER] start-server.bat konnte nicht geschrieben werden!');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  PyExe: String;
begin
  if CurStep <> ssPostInstall then
    Exit;

  PyExe := '"' + ExpandConstant('{app}\python\python.exe') + '"';

  WizardForm.ProgressGauge.Min := 0;
  WizardForm.ProgressGauge.Max := 100;
  WizardForm.ProgressGauge.Position := 0;
  LogLine('Starte Einrichtung des Servers...');

  // 1) Visual C++ Runtime
  RunStreaming('"' + ExpandConstant('{tmp}\vc_redist.x64.exe') + '" /install /quiet /norestart',
               'Visual C++ Runtime', 1);

  // 2) Python embeddable entpacken
  //    (kein Installer! Das ZIP wird nur entpackt - keine Konflikte mit System-Python)
  RunStreaming('powershell -NoProfile -ExecutionPolicy Bypass -Command "' +
               'Expand-Archive -Force ''' + ExpandConstant('{tmp}\python-embed.zip') + ''' ''' + ExpandConstant('{app}\python') + '''"',
               'Python entpacken', 2);

  // ._pth Datei konfigurieren, damit pip/site-packages funktionieren
  // (direkt per Pascal geschrieben - robuster als verschachtelte PowerShell-Escapes)
  if SaveStringToFile(ExpandConstant('{app}\python\python312._pth'),
       'python312.zip' + #13#10 +
       '.' + #13#10 +
       'Lib\site-packages' + #13#10 +
       'import site' + #13#10, False) then
    LogLine('python312._pth konfiguriert')
  else
    LogLine('[FEHLER] python312._pth konnte nicht geschrieben werden!');

  // 3) pip installieren (embeddable hat kein pip - get-pip.py holt es)
  RunStreaming(PyExe + ' "' + ExpandConstant('{tmp}\get-pip.py') + '" --no-warn-script-location',
               'pip installieren', 3);

  // 4) Python-Pakete aus requirements.txt (inkl. yt-dlp, playwright, fastapi, uvicorn)
  RunStreaming(PyExe + ' -m pip install --no-warn-script-location -r "' +
               ExpandConstant('{app}\LocalServer\requirements.txt') + '"',
               'Python-Pakete installieren', 4);

  // 5) ffmpeg entpacken -> {app}\ffmpeg\ (ffmpeg.exe UND ffprobe.exe)
  RunStreaming('powershell -NoProfile -ExecutionPolicy Bypass -Command "' +
               'Expand-Archive -Force ''' + ExpandConstant('{tmp}\ffmpeg.zip') + ''' ''' + ExpandConstant('{tmp}\ffmpeg-x') + '''; ' +
               '$bin = (Get-ChildItem -Recurse ''' + ExpandConstant('{tmp}\ffmpeg-x') + ''' -Filter ffmpeg.exe | Select-Object -First 1).DirectoryName; ' +
               'Copy-Item \"$bin\ffmpeg.exe\"  -Destination ''' + ExpandConstant('{app}\ffmpeg\ffmpeg.exe') + ''' -Force; ' +
               'Copy-Item \"$bin\ffprobe.exe\" -Destination ''' + ExpandConstant('{app}\ffmpeg\ffprobe.exe') + ''' -Force"',
               'ffmpeg einrichten', 5);

  // 6) Playwright-Browser (Chromium)
  RunStreaming(PyExe + ' -m playwright install chromium', 'Browser (Chromium) laden', 6);

  // --- Nach den Downloads: Konfigurationsdateien erzeugen ---
  LogLine('');
  LogLine('=== Konfiguration ===');
  CreateEnvFile();
  CreateStartScript();

  WizardForm.StatusLabel.Caption := 'Fertig.';
  LogLine('');
  LogLine('Server erfolgreich eingerichtet!');
  LogLine('Starten mit: start-server.bat');
end;
