; ============================================================
;  PyScrapper Desktop - Standalone Installer (Inno Setup)
;  NUR die Desktop-App: publish-Binaries + Runtimes + ffprobe
;  KEIN Python, KEIN pip, KEIN Playwright, KEINE requirements.txt
;  Kompilieren: Inno Setup oeffnen -> F9   |   ISCC.exe desktop-installer.iss
; ============================================================

#define MyAppName        "PyScrapper"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Leon Brandstetter"
#define MyAppExeName     "PyScrapperDesktopApp.exe"

; ---- WICHTIG: Pfad zum publish-Ordner (dotnet publish Output!) ----
#define MyAppPublishDir  "C:\Users\p50232\RiderProjects\PyScrapper\PyScrapperDesktopApp\bin\Release\net9.0\publish"

[Setup]
AppId={{C9E6B4F1-5D3A-4A0C-B18E-4F7D0C3E2F96}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}

PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\PyScrapper
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}

Compression=lzma2/fast
SolidCompression=no
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputBaseFilename=PyScrapper-Desktop-Setup-{#MyAppVersion}
OutputDir=installer-output

UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
CloseApplications=yes

WizardSizePercent=120

[Languages]
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; --- Die komplette publish-Ausgabe 1:1 kopieren (inkl. libvlc, runtimes) ---
; NICHT umsortieren! Die Struktur muss exakt wie im publish-Ordner bleiben.
Source: "{#MyAppPublishDir}\*"; DestDir: "{app}"; \
    Excludes: "*.pdb"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

[Dirs]
Name: "{app}\ffmpeg"

[Icons]
Name: "{group}\{#MyAppName}";                Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\ffmpeg"
Type: dirifempty; Name: "{app}"

; ============================================================
;  Code: Download + Live-Installation der Runtimes
; ============================================================
[Code]
function SendMessage(hWnd: Integer; Msg: Integer; wParam: Integer; lParam: Integer): Integer;
  external 'SendMessageW@user32.dll stdcall';

const
  EM_SCROLLCARET = $00B7;
  STEP_COUNT     = 3;

  VCREDIST_URL = 'https://aka.ms/vs/17/release/vc_redist.x64.exe';
  DOTNET_URL   = 'https://aka.ms/dotnet/9.0/windowsdesktop-runtime-win-x64.exe';
  FFMPEG_URL   = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip';

var
  DownloadPage: TDownloadWizardPage;
  LogMemo: TNewMemo;
  DotNetAlreadyInstalled: Boolean;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

// Prueft ob die .NET 9 Desktop Runtime bereits installiert ist
function IsDotNet9DesktopInstalled(): Boolean;
var
  ResultCode: Integer;
  TmpFile: String;
  Output: AnsiString;
begin
  Result := False;
  TmpFile := ExpandConstant('{tmp}\dotnet_check.txt');
  if Exec(ExpandConstant('{cmd}'),
          '/C dotnet --list-runtimes > "' + TmpFile + '" 2>&1',
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if LoadStringFromFile(TmpFile, Output) then
      Result := Pos('Microsoft.WindowsDesktop.App 9.', String(Output)) > 0;
  end;
end;

procedure InitializeWizard;
begin
  DotNetAlreadyInstalled := IsDotNet9DesktopInstalled();

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
    DownloadPage.Add(VCREDIST_URL, 'vc_redist.x64.exe', '');
    // .NET Runtime nur laden wenn noch nicht installiert
    if not DotNetAlreadyInstalled then
      DownloadPage.Add(DOTNET_URL, 'dotnet-runtime.exe', '');
    DownloadPage.Add(FFMPEG_URL, 'ffmpeg.zip', '');
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

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep <> ssPostInstall then
    Exit;

  WizardForm.ProgressGauge.Min := 0;
  WizardForm.ProgressGauge.Max := 100;
  WizardForm.ProgressGauge.Position := 0;
  LogLine('Starte Einrichtung der Komponenten...');

  // 1) Visual C++ Runtime (fuer libvlc)
  RunStreaming('"' + ExpandConstant('{tmp}\vc_redist.x64.exe') + '" /install /quiet /norestart',
               'Visual C++ Runtime', 1);

  // 2) .NET 9 Desktop Runtime (nur falls nicht vorhanden)
  if DotNetAlreadyInstalled then
  begin
    LogLine('');
    LogLine('=== .NET 9 Desktop Runtime ===');
    LogLine('Bereits installiert - wird uebersprungen.');
    SetStepProgress(2);
  end
  else
    RunStreaming('"' + ExpandConstant('{tmp}\dotnet-runtime.exe') + '" /install /quiet /norestart',
                 '.NET 9 Desktop Runtime', 2);

  // 3) ffmpeg + ffprobe entpacken -> {app}\ffmpeg\ (fuer Codec-Pruefung im AudioPlayer)
  RunStreaming('powershell -NoProfile -ExecutionPolicy Bypass -Command "' +
               'Expand-Archive -Force ''' + ExpandConstant('{tmp}\ffmpeg.zip') + ''' ''' + ExpandConstant('{tmp}\ffmpeg-x') + '''; ' +
               '$bin = (Get-ChildItem -Recurse ''' + ExpandConstant('{tmp}\ffmpeg-x') + ''' -Filter ffmpeg.exe | Select-Object -First 1).DirectoryName; ' +
               'Copy-Item \"$bin\ffmpeg.exe\"  -Destination ''' + ExpandConstant('{app}\ffmpeg\ffmpeg.exe') + ''' -Force; ' +
               'Copy-Item \"$bin\ffprobe.exe\" -Destination ''' + ExpandConstant('{app}\ffmpeg\ffprobe.exe') + ''' -Force"',
               'ffmpeg/ffprobe einrichten', 3);

  WizardForm.StatusLabel.Caption := 'Fertig.';
  LogLine('');
  LogLine('Desktop-App erfolgreich eingerichtet!');
end;
