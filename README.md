# PyScrapper – Entwickler-README

Diese Datei richtet sich **ausschließlich an Entwickler**. Sie beschreibt den aktuellen Stand der Codebasis, die Architektur, die echten Einstiegspunkte, die verfügbaren Funktionen und die wichtigsten Abweichungen zwischen Dokumentation und Code.

**Repository:** [github.com/lbrandstaetterhtl/PyScrapper](https://github.com/lbrandstaetterhtl/PyScrapper)

**Falls Sie einen Release testen oder benutzen wollen:** (neueste version) [github.com/lbrandstaetterhtl/PyscrapperInstaller/release/tag/v1.0.1](https://github.com/lbrandstaetterhtl/PyscrapperInstaller/releases/tag/v1.0.0)

**Desktop-Dokumentation (Portal):** [`PyScrapperDesktopApp/Doku_final/Index.html`](PyScrapperDesktopApp/Doku_final/Index.html)

---

## Kurzfazit zum aktuellen Stand

**Was aktuell tatsächlich im Code steckt:**

- ein lokaler **FastAPI-Server** in `LocalServer/server.py`
- eine gemeinsame Python-Business-Logik in `PythonModule/`
- eine **Desktop-App mit Avalonia / .NET 9** in `PyScrapperDesktopApp/`
- ein **React / TypeScript / Vite**-Web-Frontend in `PyScrapperWebInterface/`
- ein **SQLite-Datenmodell** im Backend (`LocalServer/Data/data.db`)
- lokale Laufzeit- und App-Logs
- **zwei getrennte Inno-Setup-Installer**: `desktop-installer.iss` (nur Desktop-App + Runtimes) und `server-installer.iss` (nur Backend mit eigenem embeddable Python)

**Wichtige Code-Realität, die man kennen muss:**

- Die Desktop-App startet den LocalServer **nicht mehr automatisch** im aktiven Codepfad. Die Startlogik existiert noch in `App.axaml.cs`, ist aber kommentiert bzw. nicht aktiv.
- Das Web-Frontend verwendet seine Fetch-URLs derzeit fest auf `http://127.0.0.1:8000`, während Backend und Desktop-Client standardmäßig mit **8765** arbeiten.
- Die Suno-Suche ist im Backend aktuell ein **Platzhalter** und liefert leere Ergebnisse.
- `/command` unterstützt aktuell nur `quit`.
- Mehrere Admin-/CRUD-Endpunkte sind über `ADMIN_KEY` abgesichert, der aus einer `.env` geladen wird. Der Server-Installer generiert diesen Key automatisch.
- Der Server ist **nur lokal gedacht** und nicht für öffentliches Deployment gehärtet.

---

## Installation über die Installer (Endnutzer, Windows x64)

Für die Installation auf **Windows x64** gibt es **zwei getrennte Inno-Setup-Bootstrapper**:

| Installer | Skript | Installiert | Zielordner (Standard) |
|---|---|---|---|
| **Desktop-App** | `desktop-installer.iss` | Avalonia-Client + Runtimes + ffmpeg/ffprobe | `%LOCALAPPDATA%\Programs\PyScrapper` |
| **Server** | `server-installer.iss` | FastAPI-Backend + eigenes Python + ffmpeg + Playwright | `%LOCALAPPDATA%\Programs\PyScrapperServer` |

Beide Installer laufen **ohne Adminrechte** (`PrivilegesRequired=lowest`) und installieren pro Benutzer nach `%LOCALAPPDATA%\Programs\`. Beide zeigen während der Einrichtung ein **Live-Konsolen-Log** und **Fortschritt pro Schritt**.

> **Warum LocalAppData statt Program Files?** Ohne Adminrechte ist `Program Files` nicht beschreibbar. Frühere Installer-Versionen scheiterten daran still (Python landete nie im Zielordner). `%LOCALAPPDATA%\Programs\` ist der korrekte Ort für Per-User-Installationen.

### Desktop-Installer (`desktop-installer.iss`)

Installiert **ausschließlich** was die Desktop-App braucht — kein Python, kein pip, kein Playwright.

**Kopierte Dateien:** Der komplette `dotnet publish`-Output (inkl. `libvlc\` und `runtimes\`) wird 1:1 nach `{app}` kopiert. Die Struktur des publish-Ordners darf nicht verändert werden, sonst findet die framework-dependent App ihre nativen Bibliotheken nicht.

**Einrichtungsschritte (3):**

1. **Visual C++ Runtime** – `vc_redist.x64.exe /install /quiet /norestart` (für libvlc)
2. **.NET 9 Desktop Runtime** – wird nur heruntergeladen und installiert, **falls nicht vorhanden** (Check via `dotnet --list-runtimes` auf `Microsoft.WindowsDesktop.App 9.x`)
3. **ffmpeg + ffprobe** – ZIP entpacken, beide Binaries nach `{app}\ffmpeg\` (ffprobe wird vom Codec-Konverter der App benötigt)

**Download-Quellen:**

- Visual C++ Redistributable x64 – `https://aka.ms/vs/17/release/vc_redist.x64.exe`
- .NET 9 Desktop Runtime x64 – `https://aka.ms/dotnet/9.0/windowsdesktop-runtime-win-x64.exe`
- ffmpeg (release-essentials) – `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip`

### Server-Installer (`server-installer.iss`)

Installiert **ausschließlich** das Backend — keine .NET-Runtime, keine Desktop-Binaries.

**Kopierte Dateien:**

- `LocalServer\` → `{app}\LocalServer\` (ohne `.venv`, `__pycache__`, `.env`, `logs`, `Data\*.db`)
- `PythonModule\` → `{app}\PythonModule\` (als **Geschwister** von `LocalServer` — zwingend, da `server.py` per `sys.path.insert` den Parent-Ordner in den Modulpfad legt)

**Einrichtungsschritte (6):**

1. **Visual C++ Runtime** – `vc_redist.x64.exe /install /quiet /norestart`
2. **Python 3.12.7 embeddable** – ZIP wird nach `{app}\python` **entpackt** (kein Installer!), danach wird `python312._pth` so konfiguriert, dass `Lib\site-packages` und `import site` aktiv sind
3. **pip installieren** – via `get-pip.py` (das embeddable Package enthält kein pip)
4. **Python-Pakete** – `python -m pip install -r {app}\LocalServer\requirements.txt`
5. **ffmpeg + ffprobe** – ZIP entpacken, beide Binaries nach `{app}\ffmpeg\`
6. **Chromium laden** – `python -m playwright install chromium` (für den Bandcamp-Fallback)

**Nach den Schritten erzeugt der Installer:**

- `{app}\LocalServer\.env` mit einem **zufällig generierten `ADMIN_KEY`** (32 Hex-Zeichen)
- `{app}\start-server.bat` – startet den Server mit dem eingebetteten Python; ffmpeg wird für die Session in den PATH gelegt

**Download-Quellen:**

- Visual C++ Redistributable x64 – `https://aka.ms/vs/17/release/vc_redist.x64.exe`
- Python 3.12.7 embeddable (amd64) – `https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip`
- get-pip – `https://bootstrap.pypa.io/get-pip.py`
- ffmpeg (release-essentials) – `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip`

> **Warum embeddable statt regulärer Python-Installer?** Der reguläre Installer (`python-3.12.7-amd64.exe /quiet TargetDir=...`) ignoriert `TargetDir` stillschweigend, wenn dieselbe Python-Version bereits auf dem System existiert (z. B. aus dem Microsoft Store) — er repariert dann die vorhandene Installation und der Zielordner bleibt leer. Das embeddable ZIP wird nur entpackt: keine Registry, keine Konflikte, funktioniert unabhängig vom Systemzustand.

> **Warum kein venv?** `{app}\python` ist bereits ein vollständig privates Python — pip installiert alle Pakete in dessen `Lib\site-packages`, isoliert vom System. Ein venv würde diese Isolation redundant nachbauen. Die `start-server.bat` ruft `python.exe` mit vollem Pfad auf; eine „Aktivierung" ist nicht nötig.

### Setup-EXEs selbst bauen

Im Repository liegen **keine fertigen Setup-EXEs** — nur die beiden `.iss`-Skripte. Wer die Installer nutzen will, baut sie selbst:

**Voraussetzung:** [Inno Setup](https://jrsoftware.org/isinfo.php) **6.1+** installiert.

1. Repository klonen und Desktop-App publishen:
```powershell
   git clone https://github.com/lbrandstaetterhtl/PyScrapper.git
   Set-Location PyScrapper
   dotnet publish PyScrapperDesktopApp -c Release --self-contained false
```

2. In beiden `.iss`-Dateien die Pfad-Defines an den eigenen Klon-Ort anpassen (`MyAppPublishDir` in `desktop-installer.iss`, `ProjectRoot` in `server-installer.iss`).
3. Beide Installer kompilieren:
```powershell
   ISCC.exe server-installer.iss
   ISCC.exe desktop-installer.iss
```

Alternativ die `.iss` in der Inno-Setup-IDE öffnen und mit **F9** kompilieren. Beide Setups landen in `installer-output\`.

4. Installieren — **erst Server, dann Desktop**:
   - `PyScrapper-Server-Setup-<version>.exe` ausführen, dem Assistenten folgen (Download-Phase, dann Einrichtung mit Live-Log).
   - Server über den Startmenü-Eintrag **„PyScrapper Server starten"** oder `{app}\start-server.bat` starten (`http://127.0.0.1:8765`).
   - `PyScrapper-Desktop-Setup-<version>.exe` ausführen.
   - Desktop-App über Startmenü oder Desktop-Icon starten — sie erwartet den laufenden Server.
     Details zu den Build-Schritten stehen im Abschnitt [Installer bauen und veröffentlichen](#installer-bauen-und-veröffentlichen).


### Ergebnisstruktur nach Installation

**Desktop (`%LOCALAPPDATA%\Programs\PyScrapper\`):**

```text
PyScrapper/
├── PyScrapperDesktopApp.exe
├── *.dll                        # Avalonia, LibVLCSharp, ...
├── libvlc\                      # native VLC-Binaries (win-x64 / win-x86)
├── runtimes\                    # native .NET-Abhängigkeiten
├── ffmpeg\
│   ├── ffmpeg.exe
│   └── ffprobe.exe
└── unins000.exe
```

**Server (`%LOCALAPPDATA%\Programs\PyScrapperServer\`):**

```text
PyScrapperServer/
├── LocalServer\
│   ├── server.py
│   ├── requirements.txt
│   ├── .env                     # generierter ADMIN_KEY
│   ├── Data\                    # SQLite-DB entsteht beim ersten Start
│   └── logs\
├── PythonModule\                # Geschwister von LocalServer (sys.path!)
├── python\                      # embeddable Python 3.12.7 + site-packages
├── ffmpeg\
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── logs\
├── data\
├── start-server.bat
└── unins000.exe
```

---

## Projektstruktur im aktuellen Snapshot

```text
PyScrapper/
├── LocalServer/
│   ├── server.py                # FastAPI-Backend und DB-Endpunkte
│   ├── requirements.txt         # Python-Abhängigkeiten
│   ├── Data/
│   │   └── data.db              # SQLite-Datenbank
│   ├── installer/               # .iss installer script
│   ├── logs/
│   │   └── server_runtime.log   # Server-Runtime-Log
│   ├── cookies.txt              # Cookie-Jar der gemeinsamen Session
│   ├── .env                     # Backend-Umgebung, u. a. ADMIN_KEY
│   ├── server_backup.py         # Legacy-/Sicherungsstand
│   └── server_OLD.py            # Legacy-/Sicherungsstand
│
├── PythonModule/
│   ├── core.py                  # HTTP-Helper
│   ├── Session.py               # Gemeinsame HTTP-Session mit Cookie-Jar
│   ├── emergencyBrowser.py      # Playwright-Fallback für geschützte Seiten
│   ├── models/
│   ├── providers/
│   └── serverservices/
│
├── PyScrapperDesktopApp/
│   ├── PyScrapperDesktopApp.csproj
│   ├── App.axaml / App.axaml.cs
│   ├── installer/               # .iss installer script
│   ├── Models/
│   ├── ViewModels/
│   ├── Views/
│   ├── Assets/
│   └── logs/
```

---

## Architektur-Überblick

### 1) `LocalServer` – FastAPI-Backend

Das Backend ist der zentrale Dienst für Suche, Download, Login/Registrierung und Datenbankzugriffe.

**Technik:**

- Python
- FastAPI + Uvicorn
- Pydantic
- SQLite
- `asyncio`
- `yt-dlp`
- `playwright`
- `bcrypt`
- `dotenv`

**Laufzeitverhalten:**

- Der Server erzeugt beim Start seine Tabellen automatisch, falls sie fehlen.
- Es gibt eine globale `Session`-Instanz mit Cookie-Persistenz.
- Downloads laufen als asynchrone Jobs und werden über UUIDs verfolgt.
- Parallel-Downloads sind über `asyncio.Semaphore(50)` begrenzt.
- Laufzeitlogs werden in `LocalServer/logs/server_runtime.log` geschrieben.

**CORS:**

Erlaubt sind derzeit nur:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

---

### 2) `PythonModule` – gemeinsame Logik

Hier steckt die eigentliche Business-Logik, die sowohl vom Server als auch indirekt vom Backend-Flow genutzt wird.

Enthalten sind:

- `core.py` – HTML-Fetching und Datei-Download-Helper
- `Session.py` – Cookie-Jar, SSL-Context über `certifi`, gemeinsame `urllib`-Session
- `emergencyBrowser.py` – Fallback-Browser für Seiten mit Bot-Schutz
- `models/` – Requests, Responses, Exceptions, Settings
- `providers/` – provider-spezifische Suche und Downloads
- `serverservices/` – Search-/Download-/Command-Orchestrierung und Hilfsfunktionen

**Prinzipien im Code:**

- keine globalen Netzwerkaufrufe beim Import
- Exceptions werden an die aufrufende Schicht durchgereicht
- Provider-Logik ist getrennt und testbar

---

### 3) `PyScrapperDesktopApp` – Desktop-Client

Die Desktop-App ist ein Avalonia-Client für Windows / .NET 9.

**Technik:**

- Avalonia 11.3.8
- .NET 9
- CommunityToolkit.Mvvm
- FluentAvaloniaUI
- LibVLCSharp
- Microsoft.Data.Sqlite
- VideoLAN.LibVLC.Windows
- DotNetEnv

**Wichtige Besonderheit:**

Die aktive Codebasis geht aktuell davon aus, dass der LocalServer bereits läuft. Die frühere automatische Server-Startlogik ist im Code zwar noch vorhanden, wird aber nicht mehr aktiv genutzt.

---

### 4) `PyScrapperWebInterface` – Web-Frontend

Ein experimentelles Web-Frontend auf Basis von React, TypeScript und Vite.

**Aktueller Funktionsumfang im UI:**

- Suchformular
- Ergebnisliste
- Download-Anfragepanel
- Fortschrittsanzeige
- Infotext / Home-Panel

**Aktuelle Einschränkung:**

Die Fetch-Requests sind im Snapshot fest auf Port `8000` verdrahtet, obwohl das Backend in den restlichen Komponenten auf `8765` läuft.

---

## Backend-Dokumentation (`LocalServer/server.py`)

### Start / Runtime

Der Server wird direkt mit Uvicorn gestartet. Es gibt im aktuellen Snapshot **keine** eingebauten Start-/Stop-Skripte im Ordner `LocalServer/scripts/...` — bei installierter Version übernimmt `start-server.bat` den Start.

Empfohlener Start aus `LocalServer/` (Entwicklungsumgebung):

```powershell
Set-Location C:\Users\p50232\RiderProjects\PyScrapper\LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Falls Bandcamp-/Browser-Fallback benötigt wird, einmalig zusätzlich:

```powershell
python -m playwright install
```

---

### Backend-Umgebung

`server.py` lädt per `load_dotenv()` eine `.env` und erwartet dort mindestens:

- `ADMIN_KEY`

In der Entwicklungsumgebung liegt die `.env` in `LocalServer/`; bei installierter Version generiert der Server-Installer sie dort automatisch mit einem zufälligen Key. Zusätzlich verwendet die Server-Session eine `cookies.txt`-Datei als Cookie-Jar.

**Wichtig:**

- Der Server ist auf lokale Nutzung ausgelegt.
- Admin-Endpunkte prüfen `ADMIN_KEY`.
- Der Server arbeitet mit HTTPS-Validierung; `http://`-URLs werden abgewiesen.

---

### Datenbank

Die SQLite-Datenbank liegt hier:

- `LocalServer/Data/data.db`

Beim Start werden folgende Tabellen angelegt, falls nicht vorhanden:

- `Users`
- `DownloadedMedias`
- `Playlists`
- `PlaylistMedias`
- `Settings`

**Bemerkungen:**

- Foreign Keys sind aktiv.
- Journal Mode ist auf `WAL` gesetzt.
- `create_app_tables()` läuft beim Startup und kann zusätzlich per Admin-Endpoint aufgerufen werden.

---

### Antwort- und Statuslogik

Der Server führt pro Download-Job eine Fortschrittsstruktur, deren Felder u. a. sind:

- `id`
- `status`
- `downloadProgress`
- `errorMessage`
- `totalBytes`
- `downloadedBytes`
- `speed`
- `eta`

Abgeschlossene oder fehlerhafte Jobs werden nach etwa **60 Sekunden** aus dem Progress-Cache entfernt.

---

### Öffentliche Haupt-Endpunkte

| Methode | Pfad | Zweck | Hinweis |
|---|---|---|---|
| GET | `/` | Startbestätigung | Gibt `Server startup successful!` zurück |
| GET | `/health` | Health / Monitoring | Uptime, RAM, PID, Prozesse, aktive Downloads, Fehlertexte |
| POST | `/command` | Steuerkommando | Aktuell nur `quit` |
| POST | `/download` | Download-Job starten | Gibt Job-ID zurück |
| GET | `/download/progress/{task_id}` | Fortschritt eines Jobs | Liefert die aktuelle Progress-Struktur |
| POST | `/search` | Suche | Provider-spezifische Suche |
| POST | `/login` | Login | Gegen die `Users`-Tabelle |
| POST | `/register` | Registrierung | Legt einen User über denselben Mechanismus wie Create-User an |
| POST | `/save/{key}` | User Daten speichern | Speichert die Daten eines Users per user_identifier (ist nicht fertig und sehr instabil) |

**Hinweis zu `/command`:**

Aktuell ist nur `quit` erlaubt. Andere Kommandos führen zu `CommandError`.

---

### Admin- und CRUD-Endpunkte

Die folgenden Endpunkte sind durch `ADMIN_KEY` geschützt oder dienen DB-Verwaltungszwecken:

#### Users

- `GET /get/user/{identifier}` – User per Identifier **oder** Username laden
- `GET /getall/users/{key}` – alle Users laden
- `POST /create-tables/{key}` – Tabellen neu anlegen
- `POST /create/user/{key}` – User anlegen
- `POST /delete/user/{key}` – User löschen

#### Playlists

- `GET /get/playlists/{identifier}` – Playlist per Identifier laden
- `GET /getall/playlists/{key}` – alle Playlists laden
- `GET /getuser/playlists/{key}` – alle Playlists eines Users laden
- `POST /create/playlist/{key}` – Playlist anlegen
- `POST /delete/playlist/{key}` – Playlist löschen

#### Downloaded Medias

- `GET /get/downloadedmedia/{identifier}` – einzelnes Medium laden
- `GET /getall/downloadedmedias/{key}` – alle Medien laden
- `GET /getuser/downloadedmedias/{key}` – Medien eines Users laden
- `POST /create/downloadedmedia/{key}` – Medium anlegen
- `POST /delete/downloadedmedia/{key}` – Medium löschen

#### Settings

- `GET /get/settings/{user_identifier}` – Settings eines Users laden
- `GET /getall/settings/{key}` – alle Settings laden
- `POST /create/settings/{key}` – Settings anlegen
- `POST /delete/settings/{key}` – Settings löschen

#### Playlist-Medien

- `GET /get/playlistmedias/{playlist_identifier}` – Medien einer Playlist laden
- `POST /create/playlistmedia/{key}` – Medium zur Playlist hinzufügen
- `POST /delete/playlistmedia/{key}` – Medium aus Playlist entfernen

---

### Download-/Search-Validierung

Der Backend-Code prüft vor dem Download unter anderem:

- Provider-Namen über Alias-Listen
- erlaubte Media-Typen pro Provider
- HTTPS-URLs
- ob die Ziel-Datei schon existiert
- ob die URL überhaupt erreichbar ist

**Provider-Aliases im Code:**

- `archive`: `archive`, `archive.org`, `www.archive.org`, `internetarchive`
- `youtube`: `youtube`, `youtube.com`, `www.youtube.com`
- `suno`: `suno`, `suno.com`, `www.suno.com`
- `bandcamp`: `bandcamp`, `band-camp`, `bandcamp.com`, plus ein aktuell falsch geschriebener Legacy-Alias im Code

**Hinweis:**

Im Zweifel immer die kanonischen Provider-Namen verwenden:

- `archive`
- `bandcamp`
- `youtube`
- `suno`

---

### Unterstützte Provider und Formate

| Provider | Suche | Download | Unterstützte Formate | Bemerkungen |
|---|---:|---:|---|---|
| `archive` | Ja | Ja | `.mp3`, `.mp4`, `.wav`, `.mkv` | Suche via archive.org advanced search, Download über Metadata |
| `youtube` | Ja | Ja | `.mp3`, `.mp4` | Audio-Download mit FFmpeg-Extraktion, Video-Download via `yt-dlp` |
| `bandcamp` | Ja | Ja | `.mp3` | Bei 403 kann ein Playwright-Fallback ausgelöst werden; Album-URLs sind aktuell nicht unterstützt |
| `suno` | Download ja, Suche aktuell nein | Ja | Code validiert `.mp3`, `.mp4`, `.wav` | Die Suche liefert aktuell leere Ergebnisse; WAV-Unterstützung ist im Code inkonsistent und eher experimentell |

---

### Provider-Details

#### `archive`

- Suchfunktion nutzt die Archive-Advanced-Search API
- Download nutzt Metadaten und lädt die erste passende Datei mit gewünschtem Suffix
- Fortschritt wird anhand der Content-Length berechnet

#### `youtube`

- Suche parst `ytInitialData`
- Download via `yt-dlp`
- Audio-Only wird nach MP3 extrahiert
- Video-Download wird als MP4 gemerged
- FFmpeg wird automatisch gesucht (`PATH` / WinGet-Installation)

#### `bandcamp`

- Suche parst die Suchergebnisseite von Bandcamp
- Track-URLs werden auf Streaming-URLs aufgelöst
- Bei 403 kann ein Playwright-basierter Fallback die Wiedergabe initialisieren
- Album-URLs sind im Downloadpfad aktuell explizit nicht unterstützt

#### `suno`

- Download sucht Song-Medien direkt auf der Suno-Seite
- Creator-Seiten werden unterstützt
- Suche ist im aktuellen `SearchProcessor` noch ein Platzhalter und liefert `{}`

---

## Gemeinsame Python-Module (`PythonModule/`)

### `core.py`

Enthält zwei wichtige Helfer:

- `get_html(...)` – holt HTML über die gemeinsame Session
- `download_to_file(...)` – streamt Daten in eine Datei und aktualisiert Progress-Werte

### `Session.py`

Die Session verwendet:

- `MozillaCookieJar`
- `certifi`-basierten SSL-Context
- gemeinsame Headers / User-Agent

Cookies werden persistiert, sobald die Session benutzt wird.

### `serverservices/`

- `searchProcessor.py` – routet Suche auf Provider
- `downloadProcessor.py` – routet Downloads auf Provider und hält den Semaphore-Mechanismus
- `commandProcessor.py` – verarbeitet Steuerkommandos, aktuell nur `quit`
- `utils.py` – Provider- und URL-Validierung, Dateipfad-Erzeugung, Cleanup

### `models/`

- `requests.py` – Request-Modelle für Download, Search, Login, Register, CRUD
- `responses.py` – Antwortmodelle für API-Responses
- `settings.py` – Provider-/Dateityp-Listen, Progress-Default, Kommandos
- `exceptions.py` – gemeinsame Exception-Typen

---

## Desktop-App-Dokumentation (`PyScrapperDesktopApp/`)

### Tech-Stack

- `net9.0`
- Avalonia UI
- MVVM via CommunityToolkit.Mvvm
- LibVLCSharp / VideoLAN.LibVLC.Windows
- SQLite via `Microsoft.Data.Sqlite`
- `DotNetEnv` für `.env`-Laden
- `FluentAvaloniaUI`

### Projektverhalten beim Start

Die App geht im aktuellen Stand in dieser Reihenfolge vor:

1. Login-Fenster anzeigen
2. Benutzer gegen den LocalServer anmelden oder registrieren
3. Settings vom Backend laden
4. Falls keine Settings existieren, Default-Settings anlegen
5. Launcher-Fenster zur Umgebungsvorbereitung anzeigen
6. Danach Main Window öffnen

**Wichtig:**

- Wenn der Backend-Server nicht erreichbar ist, schlägt der Launcher aktuell fehl.
- Die ehemals kommentierte Auto-Start-Logik für den Server ist nicht aktiv.

### Was die Launcher-Phase prüft / vorbereitet

- ob der Server erreichbar ist
- Visual C++ Redistributable-Check
- FFmpeg-Check
- Python-Installation / Version
- `pip`
- virtuelle Umgebung
- Python-Requirements
- Playwright-Browser
- `dotnet restore` für die .NET-Projekte

> **Verhältnis zu den Installern:** Bei einer Installation über die beiden Installer sind Visual C++, .NET-Runtime, ffmpeg (Desktop) bzw. Python, Requirements und der Playwright-Browser (Server) bereits eingerichtet. Die Launcher-Phase findet diese Komponenten dann vor und muss sie nicht erneut installieren – sie prüft im Wesentlichen nur noch die Server-Erreichbarkeit. **Hinweis:** Die Python-/venv-/pip-Checks des Launchers beziehen sich auf die Dev-Umgebung; bei installierter Version liegen diese Komponenten in der Server-Installation und sind aus Sicht der Desktop-App nicht relevant.

### Wichtige Fenster / Views

Aktuell existieren u. a. diese Views:

- `LoginWindow`
- `LauncherWindow`
- `MainWindow`
- `SunoScrapWindow`
- `ScrapWindowWithSearch`
- `ProgressBarWindow`
- `GetServerHealthWindow`
- `LogsWindow`
- `CodecConverterWindow`
- `CreatePlaylistWindow`
- `PlaylistDetailsWindow`
- `FilterWindow`
- `ConfirmationWindow`
- `InputWindow`
- `MessageBox`
- `MediaPlayerControl` als wiederverwendbare Kontrolle

### Hauptfunktionen der Desktop-App

- Login / Registrierung gegen das Backend
- lokale Anzeige der heruntergeladenen Medien
- Suche + Download für YouTube, Bandcamp und Archive
- Suno-Download per Direkt-URL
- Health-Ansicht des Servers
- Log-Viewer für App- und Server-Logs
- Playlist-Erstellung und Playlist-Verwaltung
- Medienfilter und Sortierung
- Theme-Umschaltung (Dark/Light)
- Folder-Scan-Option beim Start
- integrierte Medienwiedergabe über LibVLC
- Codec-Konvertierung via FFmpeg / FFprobe

### Medienplayer / Konvertierung

**Medienplayer:**

- basiert auf LibVLCSharp
- unterstützt Audio und Video
- Shuffle / nächste / vorherige Titel / Seek / Volume / Compact-Mode etc.

**Codec-Konverter:**

- nutzt `ffprobe` zur Laufzeitbestimmung der Mediendauer
- startet `ffmpeg`
- konvertiert inkompatible Medien nach H.264 / AAC MP4
- speichert das Ergebnis als neuen Medien-Datensatz in der App-Datenbank

### Lokale Desktop-Daten

Die App nutzt keine JSON-Dauerpersistenz für die Medienbibliothek; sie arbeitet mit der Backend-DB und hält Laufzeitdaten in `AppData`.

Wichtige lokale Pfade:

- `PyScrapperDesktopApp/logs/app.log`
- `PyScrapperDesktopApp/Assets/`
- `PyScrapperDesktopApp/data/` ist im Code als Datenpfad vorgesehen

### Environment / `.env`

Die Desktop-App lädt per `DotNetEnv` die `.env` aus dem Repository-Root und erwartet dort `ADMIN_KEY`.

Wenn dieser Wert fehlt, wirft `AppData` beim Initialisieren eine Exception.

---

## Web-Frontend-Dokumentation (`PyScrapperWebInterface/`)

### Aktueller Funktionsumfang

Das Web-Frontend ist ein schlanker UI-Shell für:

- Suche
- Ergebnisanzeige
- Auswahl eines Suchtreffers
- Download-Anfrage
- Fortschrittsanzeige
- Infobox / Home-Text

### Aktuell unterstützte Provider im Web UI

Im Web-Frontend sind derzeit nur diese Provider modelliert:

- `youtube`
- `archive`
- `bandcamp`

### Aktuelle technische Details

- React 19
- TypeScript
- Vite
- `npm run dev` startet den Dev-Server mit Host `0.0.0.0`
- `npm run build` kompiliert TypeScript und erzeugt den Vite-Build

### Wichtige Mismatch-Stelle

Die Web-Fetch-Helfer sind derzeit fest auf `http://127.0.0.1:8000` verdrahtet:

- `src/components/fetchRequests/searchRequest.ts`
- `src/components/fetchRequests/downloadRequest.ts`
- `src/components/fetchRequests/downloadProgressRequest.ts`

Das bedeutet:

- Entweder muss der Backend-Port angepasst werden,
- oder das Web-Frontend braucht einen Proxy / eine Umverdrahtung auf `8765`.

### Web-Setup

```powershell
Set-Location C:\Users\p50232\RiderProjects\PyScrapper\PyScrapperWebInterface
npm install
npm run dev
```

Build:

```powershell
npm run build
```

Optional lint:

```powershell
npm run lint
```

---

## Empfohlene Setup-Schritte

> Diese Schritte richten die Umgebung **manuell** für die Entwicklung ein. Endnutzer nutzen stattdessen die [beiden Installer](#installation-über-die-installer-endnutzer-windows-x64), die Runtimes, Python, ffmpeg, Requirements und Playwright automatisch einrichten.

### 1) Python-Backend vorbereiten

```powershell
Set-Location C:\Users\p50232\RiderProjects\PyScrapper\LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install
```

Start:

```powershell
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

### 2) Desktop-App starten

```powershell
Set-Location C:\Users\p50232\RiderProjects\PyScrapper\PyScrapperDesktopApp
dotnet restore
dotnet build
dotnet run
```

**Hinweis:** Der Backend-Server muss dafür bereits laufen.

### 3) Web-Frontend starten

```powershell
Set-Location C:\Users\p50232\RiderProjects\PyScrapper\PyScrapperWebInterface
npm install
npm run dev
```

Falls das Frontend gegen das Backend sprechen soll, beachte die Port-Mismatch-Stelle (`8000` vs. `8765`).

---

## Installer bauen und veröffentlichen

Voraussetzung: [Inno Setup](https://jrsoftware.org/isinfo.php) **6.1+** (wegen `WizardSizePercent`).

### Desktop-Installer bauen

1. Desktop-App frisch publishen (framework-dependent, ohne `-r`):

   ```powershell
   Set-Location C:\Users\p50232\RiderProjects\PyScrapper
   dotnet publish PyScrapperDesktopApp -c Release --self-contained false
   ```

   Ergebnis liegt in `PyScrapperDesktopApp\bin\Release\net9.0\publish\`. **Immer den publish-Ordner verwenden, nie den rohen `net9.0\`-Build-Ordner** — nur publish enthält garantiert alle Abhängigkeiten für fremde Rechner.

2. In `desktop-installer.iss` den Pfad prüfen:

   ```pascal
   #define MyAppPublishDir  "C:\...\PyScrapper\PyScrapperDesktopApp\bin\Release\net9.0\publish"
   ```

3. Kompilieren:

   ```powershell
   ISCC.exe desktop-installer.iss
   ```

### Server-Installer bauen

1. In `server-installer.iss` den Projekt-Root prüfen:

   ```pascal
   #define ProjectRoot  "C:\...\PyScrapper"
   ```

2. Kompilieren:

   ```powershell
   ISCC.exe server-installer.iss
   ```

Beide Setups landen in `installer-output\`.

### Eckdaten der Skripte

| | Desktop | Server |
|---|---|---|
| AppId | eigene GUID | eigene GUID |
| Zielordner | `{localappdata}\Programs\PyScrapper` | `{localappdata}\Programs\PyScrapperServer` |
| Kompression | `lzma2/fast` | `none` (Server-Code ist klein, Downloads dominieren) |
| Sprachen | Deutsch, Englisch | Deutsch, Englisch |
| CloseApplications | `yes` | `no` |
| Setup-Schritte | 3 | 6 |

---

## Wichtige Logs, Daten und Dateien

| Pfad | Zweck |
|---|---|
| `LocalServer/server.py` | Backend-Einstiegspunkt |
| `LocalServer/requirements.txt` | Backend-Dependencies |
| `LocalServer/Data/data.db` | SQLite-Datenbank |
| `LocalServer/logs/server_runtime.log` | Backend-Runtime-Log |
| `LocalServer/cookies.txt` | Session-Cookie-Jar |
| `LocalServer/.env` | Backend-Umgebung (`ADMIN_KEY`) |
| `PyScrapperDesktopApp/logs/app.log` | App-Log |
| `PyScrapperDesktopApp/PyScrapperDesktopApp.csproj` | Desktop-Projekt / NuGet-Pakete |
| `PyScrapperDesktopApp/bin/Release/net9.0/publish/` | Publish-Ausgabe (Quelle des Desktop-Installers) |
| `PyScrapperWebInterface/package.json` | Web-Scripts / Dependencies |
| `PyScrapperWebInterface/src/components/fetchRequests/*.ts` | Web-API-URLs |
| `desktop-installer.iss` | Inno-Setup-Skript für die Desktop-App |
| `server-installer.iss` | Inno-Setup-Skript für den Server |
| `icon.ico` | Installer- und App-Icon |
| `installer-output/` | Ausgabeordner beider kompilierten Setups |

---

## Bekannte Stolperfallen und aktuelle Einschränkungen

- Die Desktop-App startet den LocalServer aktuell **nicht** mehr selbst.
- Der Web-Client nutzt aktuell **Port 8000**, nicht 8765.
- `Suno`-Suche ist im Backend aktuell ein Platzhalter.
- Bandcamp-Album-Downloads sind aktuell nicht implementiert.
- Einige Provider-Alias-Listen enthalten Tippfehler oder Legacy-Aliases; deshalb besser die kanonischen Provider-Namen nutzen.
- `HTTP://`-Downloads werden abgelehnt, nur `HTTPS://` ist erlaubt.
- Der Server ist nur lokal gedacht und hat keine Sicherheits-Härtung für öffentliches Deployment; es fehlen u. a. Rate-Limits, harte AuthZ/ACLs und Abuse-Schutz.
- `download/progress`-Einträge werden nach dem Abschluss verzögert entfernt; wenn du Jobs debuggen willst, schau zeitnah nach.
- `ADMIN_KEY` muss sowohl im Backend- als auch im Desktop-Umfeld verfügbar sein, wenn die jeweiligen Admin-/DB-Flows genutzt werden. Bei installierter Server-Version wird der Key automatisch generiert und liegt in `{app}\LocalServer\.env`.
- `Playwright`-Browser sind für geschützte Seiten notwendig; ohne `python -m playwright install` sind Bandcamp-Fallbacks fehleranfällig.
- `FFmpeg` / `ffprobe` werden für YouTube-Downloads und Codec-Konvertierung benötigt.
- Die frühere README verwies auf Skripte unter `LocalServer/scripts/...`; diese sind im aktuellen Snapshot nicht vorhanden.
- `PlaylistDetailsWindow` ist vorhanden, aber das direkte Play-/Lookup-Wiring ist im aktuellen Stand noch nicht vollständig verdrahtet.
- **`/save/{key}` ist instabil.** Beobachtete Fehler: `FOREIGN KEY constraint failed` (meist Einfüge-Reihenfolge – `PlaylistMedias` muss nach Medien und Playlists geschrieben werden – oder Waisen-Zuordnungen auf gelöschte Medien) und `database is locked` (SQLite lässt nur einen Schreiber zu; WAL + `busy_timeout` setzen, den Save in einer Transaktion ausführen, nach Fehlern sauber `rollback`+`close`, da ein abgebrochener Save sonst eine Sperre hinterlässt).

### Installer-bezogene Stolperfallen

- **Zwei Installer, klare Trennung:** Der Desktop-Installer liefert kein Python/Playwright, der Server-Installer keine .NET-Runtime. Wer beides braucht, installiert beide.
- **Immer den publish-Ordner einpacken:** Der rohe `bin\Release\net9.0\`-Ordner funktioniert nur auf dem Entwickler-Rechner (NuGet-Cache). Für den Installer zählt ausschließlich `publish\`.
- **`SourcePath`/`PublishDir` prüfen:** Ein nicht existenter Quellpfad führt dazu, dass Inno Setup vom falschen Ort einpackt — im schlimmsten Fall vom Laufwerks-Root inklusive Systemdateien.
- **Regulärer Python-Installer ist tabu:** `TargetDir` wird bei vorhandener gleicher Python-Version ignoriert (Exit-Code trotzdem 0). Nur das embeddable ZIP ist zuverlässig.
- **`python312._pth` nicht vergessen:** Ohne `import site` + `Lib\site-packages` in dieser Datei findet das embeddable Python keine per pip installierten Pakete.
- **Verwaltete Rechner (AppLocker/SRP):** Auf Firmen-/FH-Rechnern kann „Error 5: Access is denied" beim Setup-Start auftreten — Inno entpackt sich nach `%TEMP%`, was Policies oft verbieten. Workarounds: als Administrator starten oder `TEMP`/`TMP` vor dem Start auf einen erlaubten Ordner umbiegen. Auf privaten Rechnern tritt das nicht auf.
- **ffprobe-Pfad im Code:** `AudioPlayer.cs` muss ffprobe unter `{app}\ffmpeg\ffprobe.exe` (relativ zu `AppContext.BaseDirectory`) suchen, nicht unter dem Dev-Pfad `LocalServer\ffmpeg\bin\`.
- **Download-URLs fest verdrahtet:** VC++, .NET Runtime, Python-embed, get-pip und ffmpeg werden von festen URLs geladen — ändern sich diese Upstream, müssen sie in beiden `.iss`-Dateien angepasst werden.

---

## Security Audit (kurz)

Das Projekt ist aktuell ein **lokales Entwickler-Tool** und kein gehärteter Internetdienst.

### Auffälligkeiten im aktuellen Stand

- `ADMIN_KEY` kommt aus einer lokalen `.env` und schützt mehrere Verwaltungs-Endpunkte.
- Es gibt CRUD-Endpunkte für Users, Playlists, Medien, Settings und Playlist-Medien.
- `/command` kann mit `quit` einen Shutdown auslösen.
- `/download` und `/search` erlauben externe Netzwerkzugriffe und potenziell hohen Ressourcenverbrauch.
- Es sind keine erkennbaren Schutzmechanismen wie Rate-Limits, Quotas, IP-Allowlisting oder ein dediziertes Auth-/Session-Modell pro Benutzer eingebaut.

### Warum man es nicht public hosten sollte

1. Die API enthält sensible Verwaltungsfunktionen, die bei Fehlkonfiguration direkt missbraucht werden könnten.
2. Das Backend verlässt sich stark auf lokale Vertrauensannahmen statt auf eine harte Sicherheitsgrenze.
3. Externe Scraping-/Download-Flows können schnell zu Last, Fehlern oder unerwünschtem Traffic führen.
4. Ohne zusätzliche Härtung ist die Angriffsfläche für unautorisierte Zugriffe und Missbrauch zu groß.

### Was für Public Hosting fehlen würde

- echte Authentifizierung und Autorisierung pro Route
- Request-Rate-Limits und Quoten
- zentrale Audit-Logs mit Zugriffskontrolle
- Secret-Management statt lokaler `.env`
- Proxy-/Firewall-/Reverse-Proxy-Härtung
- Input-Validation und Allowlist-Strategien für alle externen Targets

---

## Praktische Schnellkommandos

### Backend-Health prüfen

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

### Backend-Docs öffnen

```powershell
Start-Process http://127.0.0.1:8765/docs
```

### Server-Log ansehen

```powershell
Get-Content C:\Users\p50232\RiderProjects\PyScrapper\LocalServer\logs\server_runtime.log -Tail 100
```

### App-Log ansehen

```powershell
Get-Content C:\Users\p50232\RiderProjects\PyScrapper\PyScrapperDesktopApp\logs\app.log -Tail 100
```

### Desktop-Installer kompilieren

```powershell
ISCC.exe desktop-installer.iss
```

### Server-Installer kompilieren

```powershell
ISCC.exe server-installer.iss
```

---

## Schlussbemerkung

Diese README ist bewusst auf den **aktuellen Codezustand** ausgerichtet. Wenn du den Backend-Port, die Suno-Suche, den Desktop-Startflow, die Web-Frontend-URLs oder die Installer (`desktop-installer.iss` / `server-installer.iss`) änderst, sollte diese Datei als erstes mitgezogen werden.
