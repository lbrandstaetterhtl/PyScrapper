; ============================================================
;  PyScrapper – Bootstrapper-Installer (Inno Setup)
;  MIT: Fortschritt pro Schritt + Prozent, Live-Konsolen-Log, Banner/Optik
;  Kompilieren: Inno Setup öffnen -> F9   |   ISCC.exe installer.iss
; ============================================================

#define MyAppName        "PyScrapper"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Leon Brandstetter"
#define MyAppExeName     "PyScrapperDesktopApp.exe"
#define MyAppPublishDir  "win-x64"

[Setup]
AppId={{A7E4F2C9-3B1D-4E8A-9F6C-2D5B8A1E0C74}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}

PrivilegesRequired=lowest
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}

Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputBaseFilename=PyScrapper-Setup-{#MyAppVersion}
OutputDir=installer-output

SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
CloseApplications=yes

; ---------- OPTIK ----------
WizardStyle=modern
; Banner-Grafik links auf Willkommens-/Fertig-Seite (BMP, ~164x314 px, DPI-Vielfache besser)
WizardImageFile=banner.bmp
; Kleines Logo oben rechts auf den Innenseiten (BMP, ~55x58 px)
WizardSmallImageFile=logo.bmp
; Assistent vergrößern (Inno 6.1+). 120 = 20% größer. Optional:
WizardSizePercent=120
; WizardResizable=yes

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppPublishDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
; Server-Code anpassen:
; Source: "server\*"; DestDir: "{app}\server"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";                Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; ============================================================
;  Code: Download + Live-Installation
; ============================================================
[Code]
// SendMessage importieren, um das Log-Feld nach unten zu scrollen
function SendMessage(hWnd: Integer; Msg: Integer; wParam: Integer; lParam: Integer): Integer;
  external 'SendMessageW@user32.dll stdcall';

const
  EM_SCROLLCARET = $00B7;
  STEP_COUNT     = 6;              // Anzahl der Installationsschritte

  VCREDIST_URL = 'https://aka.ms/vs/17/release/vc_redist.x64.exe';
  PYTHON_URL   = 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe';
  FFMPEG_URL   = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip';

var
  DownloadPage: TDownloadWizardPage;
  LogMemo: TNewMemo;

// ---------- Download-Phase (zeigt eigenen Fortschrittsbalken mit %) ----------
function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(
    'Komponenten herunterladen',
    'Benötigte Dateien werden heruntergeladen...',
    @OnDownloadProgress);

  // Log-Feld auf der "Installieren"-Seite erzeugen (unter dem Fortschrittsbalken)
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
  LogMemo.Color := $001E1E1E;      // dunkler Hintergrund (Konsolen-Look)
  LogMemo.Font.Color := $00D4D4D4; // hellgrauer Text
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpReady then
  begin
    DownloadPage.Clear;
    DownloadPage.Add(VCREDIST_URL, 'vc_redist.x64.exe',   '');
    DownloadPage.Add(PYTHON_URL,   'python-installer.exe', '');
    DownloadPage.Add(FFMPEG_URL,   'ffmpeg.zip',           '');
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

// ---------- Hilfsfunktionen fürs Log ----------
procedure LogLine(const S: String);
begin
  LogMemo.Lines.Add(S);
  LogMemo.SelStart := Length(LogMemo.Text);
  SendMessage(LogMemo.Handle, EM_SCROLLCARET, 0, 0);
  LogMemo.Update;
end;

// Setzt den Gesamt-Fortschritt (0..100) anhand des aktuellen Schritts
procedure SetStepProgress(StepIndex: Integer);
begin
  WizardForm.ProgressGauge.Position := Round(StepIndex / STEP_COUNT * 100);
  WizardForm.Update;
end;

// Führt EINEN Befehl aus und streamt dessen Ausgabe LIVE ins Log-Feld.
// Läuft non-blocking (ewNoWait) -> Assistent bleibt bedienbar/gezeichnet.
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

  // /V:ON -> !ERRORLEVEL! (Exit-Code des Blocks) korrekt in die .done-Datei schreiben
  FullCmd := '/V:ON /C (' + CmdLine + ') > "' + LogFile + '" 2>&1 & echo !ERRORLEVEL! > "' + DoneFile + '"';
  Exec(ExpandConstant('{cmd}'), FullCmd, '', SW_HIDE, ewNoWait, ResultCode);

  LastLen := 0;
  // Solange die .done-Datei fehlt, läuft der Befehl noch -> Log mitlesen
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

  // letzte Ausgabe + Exit-Code
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

// ---------- Läuft NACH dem Kopieren der App-Dateien ----------
procedure CurStepChanged(CurStep: TSetupStep);
var
  PyExe: String;
begin
  if CurStep <> ssPostInstall then
    Exit;

  PyExe := '"' + ExpandConstant('{app}\python\python.exe') + '"';

  // Fortschrittsbalken übernehmen (Datei-Kopieren ist hier fertig)
  WizardForm.ProgressGauge.Min := 0;
  WizardForm.ProgressGauge.Max := 100;
  WizardForm.ProgressGauge.Position := 0;
  LogLine('Starte Einrichtung der Komponenten...');

  // 1) Visual C++ Runtime (windowed/still -> wenig Text im Log)
  RunStreaming('"' + ExpandConstant('{tmp}\vc_redist.x64.exe') + '" /install /quiet /norestart',
               'Visual C++ Runtime', 1);

  // 2) Python nach {app}\python (fester Pfad)
  RunStreaming('"' + ExpandConstant('{tmp}\python-installer.exe') +
               '" /quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_pip=1 TargetDir="' +
               ExpandConstant('{app}\python') + '"',
               'Python installieren', 2);

  // 3) pip aktualisieren (Live-Ausgabe)
  RunStreaming(PyExe + ' -m pip install --upgrade pip', 'pip aktualisieren', 3);

  // 4) Python-Pakete (Live-Ausgabe: hier sieht man richtig was)
  RunStreaming(PyExe + ' -m pip install --no-warn-script-location -r "' +
               ExpandConstant('{app}\requirements.txt') + '"',
               'Python-Pakete installieren', 4);

  // 5) ffmpeg entpacken -> {app}\ffmpeg.exe
  RunStreaming('powershell -NoProfile -ExecutionPolicy Bypass -Command "' +
               'Expand-Archive -Force ''' + ExpandConstant('{tmp}\ffmpeg.zip') + ''' ''' + ExpandConstant('{tmp}\ffmpeg-x') + '''; ' +
               'Copy-Item (Get-ChildItem -Recurse ''' + ExpandConstant('{tmp}\ffmpeg-x') + ''' -Filter ffmpeg.exe | Select-Object -First 1).FullName -Destination ''' + ExpandConstant('{app}\ffmpeg.exe') + ''' -Force"',
               'ffmpeg einrichten', 5);

  // 6) Playwright-Browser (Live-Ausgabe: Download-Fortschritt)
  RunStreaming(PyExe + ' -m playwright install chromium', 'Browser (Chromium) laden', 6);

  WizardForm.StatusLabel.Caption := 'Fertig.';
  LogLine('');
  LogLine('Alle Komponenten eingerichtet.');
end;
