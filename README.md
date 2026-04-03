# PyScrapper – Developer README

Diese Datei richtet sich **ausschließlich an Entwickler**.  
Sie beschreibt Architektur, Setup, typische Workflows und bekannte Stolperfallen.

---

## Projektstruktur (High Level)

```
PyScrapper/
├── LocalServer/                  # FastAPI Backend (Python)
│   ├── server.py                 # Einstiegspunkt (uvicorn app)
│   ├── requirements.txt          # Python-Abhängigkeiten
│   ├── scripts/
│   │   ├── WinScripts/           # PowerShell-Skripte (Windows)
│   │   │   ├── StartServer.ps1
│   │   │   ├── StopServer.ps1
│   │   │   ├── InstallRequirementsBackend.ps1
│   │   │   ├── InstallRequirementsFrontend.ps1
│   │   │   ├── InstallFFMPEG.ps1
│   │   │   ├── ActivateVirtualEnvironment.ps1
│   │   │   └── Common.ps1
│   │   └── LinuxScripts/         # Shell-Skripte (Linux)
│   │       ├── StartServer.sh
│   │       ├── StopServer.sh
│   │       ├── install_backend_requirements.sh
│   │       ├── install_ffmpeg.sh
│   │       ├── InstallRequirementsFrontend.sh
│   │       └── activate_venv.sh
│   ├── logs/                     # Runtime-Logs des Servers
│   └── .venv/                    # Virtuelle Umgebung (lokal, nicht eingecheckt)
│
├── PythonModule/                 # Core-Logik (Sessions, Scraping, Downloads)
│   ├── Session.py                # Gemeinsame HTTP-Session
│   ├── core.py                   # Gemeinsame HTTP-Hilfsfunktionen
│   ├── emergencyBrowser.py       # Playwright-basierter Fallback-Browser
│   ├── models/                   # Datenmodelle & Einstellungen
│   │   ├── requests.py
│   │   ├── settings.py
│   │   └── exceptions.py
│   ├── providers/                # Provider-spezifische Download-/Such-Logik
│   │   ├── Archive.py            # Internet Archive
│   │   ├── Bandcamp.py           # Bandcamp
│   │   ├── Suno.py               # suno.com
│   │   └── Youtube.py            # YouTube (via yt-dlp)
│   └── serverservices/           # Server-seitige Prozessoren
│       ├── downloadProcessor.py
│       ├── searchProcessor.py
│       ├── commandProcessor.py
│       └── utils.py
│
├── PyScrapperDesktopApp/         # Desktop Client (C# / Avalonia / .NET 9)
│   ├── *.sln / *.csproj
│   ├── Models/                   # ApiClient, AppData, AppLogger, AudioPlayer
│   ├── ViewModels/               # MVVM ViewModels
│   ├── Views/                    # Avalonia AXAML Windows
│   └── data/                     # Persistente App-Daten (downloadedMedias.json)
│
├── PyScrapperDesktopApp.Tests/   # C# Unit Tests (xUnit / Avalonia)
│   ├── ViewModels/               # ViewModel-Tests
│   └── AvaloniaFixture.cs
│
├── PyScrapperWebInterface/       # Web Frontend (React / TypeScript / Vite)
│   ├── src/
│   │   ├── components/           # React-Komponenten
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── Downloads/                    # Standard-Downloadordner für Medien
└── Notes/                        # Projektnotizen & Statistiken
```

---

## Architektur-Überblick

### LocalServer (Python / FastAPI)

- Läuft lokal via **uvicorn**
- Stellt folgende HTTP-Endpunkte bereit:

| Methode | Pfad                          | Beschreibung                                         |
|---------|-------------------------------|------------------------------------------------------|
| GET     | `/`                           | Root – Startbestätigung                              |
| GET     | `/health`                     | Uptime, RAM-Verbrauch, PID, laufende Python-Prozesse |
| POST    | `/command`                    | Queue-basierte Kommandos (z.B. `quit`)               |
| POST    | `/download`                   | Download-Job für einen URL                           |
| GET     | `/download/progress/{task_id}`| Fortschritt eines laufenden Download-Jobs            |
| POST    | `/search`                     | Suche mit konfigurierbarer Trefferanzahl             |

- Nutzt **asyncio Queues**, um Requests von der Verarbeitung zu entkoppeln
- Parallele Downloads durch `asyncio.Semaphore(50)` begrenzt
- Runtime-Logs werden in `LocalServer/logs/server_runtime.log` geschrieben
- Importiert Logik aus `PythonModule`

**Unterstützte Provider:** `suno`, `suno.com`, `youtube`, `youtube.com`, `archive`, `archive.org`, `bandcamp`

**Wichtig:**  
Der Server ist nicht gehärtet und **nicht für öffentliches Deployment gedacht**.

---

### PythonModule

- Enthält die eigentliche Business-Logik
- Kein Web-Code – wird direkt vom LocalServer importiert
- Module:
  - `Session.py` – gemeinsame HTTP-Session (Cookies etc.)
  - `core.py` – gemeinsame HTTP-Hilfsfunktionen
  - `emergencyBrowser.py` – Playwright-basierter Fallback-Browser für Seiten mit Bot-Schutz
- Unterverzeichnisse:
  - `models/` – Datenmodelle (`requests.py`, `settings.py`, `exceptions.py`)
  - `providers/` – Provider-spezifische Logik:
    - `Archive.py` – Download & Suche auf archive.org
    - `Bandcamp.py` – Download & Suche auf bandcamp.com
    - `Suno.py` – Download von suno.com
    - `Youtube.py` – Download (Audio/Video) und Suche via `yt-dlp`
  - `serverservices/` – Server-seitige Prozessoren (`downloadProcessor.py`, `searchProcessor.py`, `commandProcessor.py`, `utils.py`)
- Kann unabhängig getestet/erweitert werden

Empfehlung:
- Keine Side-Effects beim Import
- Keine globalen Netzwerk-Calls
- Exceptions sauber nach oben werfen

---

### Desktop App (C# / Avalonia / .NET 9)

- Cross-platform Desktop-Client, gebaut mit **Avalonia UI** und **MVVM**-Pattern
- Kommuniziert über HTTP mit dem LocalServer (`127.0.0.1:8765`)
- **Windows-Fenster / Views:**
  - `MainWindow` – Übersicht, Health-Check, Liste heruntergeladener Medien
  - `SunoScrapWindow` – Suno-Download per URL
  - `ScrapWindowWithSearch` – Suche & Download mit Sucheingabe (z.B. YouTube, Bandcamp, Archive)
  - `MediaPlayerWindow` – integrierter Medienplayer
  - `CodecConverterWindow` – Audio-/Video-Konvertierung
  - `CreatePlaylistWindow` – Playlist erstellen
  - `PlaylistDetailsWindow` – Playlist-Details & Verwaltung
  - `GetServerHealthWindow` – Server-Status & Health-Anzeige
  - `LogsWindow` – Server-Log-Anzeige
  - `ProgressBarWindow` – Fortschrittsanzeige für laufende Operationen
  - `ConfirmationWindow` – generisches Bestätigungsdialog-Fenster
  - `InputWindow` – generisches Eingabedialog-Fenster
  - `MessageBox` – benutzerdefinierte Message-Box
- **Medien-Wiedergabe** via **LibVLCSharp** (Audio & Video)
- Heruntergeladene Medien werden in `data/downloadedMedias.json` persistiert
- Datenbank-Unterstützung via **Microsoft.Data.Sqlite**

**NuGet-Pakete:**

| Paket                        | Version |
|------------------------------|---------|
| Avalonia                     | 11.3.8  |
| Avalonia.Desktop             | 11.3.8  |
| Avalonia.Themes.Fluent       | 11.3.8  |
| Avalonia.Fonts.Inter         | 11.3.8  |
| Avalonia.Diagnostics         | 11.3.8  |
| CommunityToolkit.Mvvm        | 8.4.0   |
| FluentAvaloniaUI             | 2.0.5   |
| LibVLCSharp                  | 3.9.6   |
| LibVLCSharp.Avalonia         | 3.9.6   |
| VideoLAN.LibVLC.Windows      | 3.0.23  |
| Microsoft.Data.Sqlite        | 10.0.5  |

---

## Entwicklungs-Setup

### Voraussetzungen

- Python **3.10+**
- Git
- .NET SDK **9.0**
- FFmpeg (wird automatisch via Skript installiert, falls nicht vorhanden)
- Windows oder Linux (PowerShell-Skripte für Windows, Shell-Skripte für Linux)

---

## LocalServer – Setup

### 1. Virtuelle Umgebung & Abhängigkeiten

Am einfachsten über das Start-Skript – es legt die `.venv` automatisch an,
aktiviert sie und installiert fehlende Pakete:

**Windows (PowerShell):**

```powershell
.\LocalServer\scripts\WinScripts\StartServer.ps1
```

**Linux (Bash):**

```bash
./LocalServer/scripts/LinuxScripts/StartServer.sh
```

Oder manuell (PowerShell):

```powershell
cd LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Python-Abhängigkeiten (`requirements.txt`):**

```
fastapi
uvicorn[standard]
pydantic
certifi
yt-dlp
playwright
```

### 2. Server starten

Über Script (empfohlen – verwaltet venv, ffmpeg und Logging automatisch):

**Windows:**
```powershell
.\LocalServer\scripts\WinScripts\StartServer.ps1
```

**Linux:**
```bash
./LocalServer/scripts/LinuxScripts/StartServer.sh
```

Direkt (wenn venv bereits aktiv):

```
uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765
```

### 3. Server stoppen

**Windows:**
```powershell
.\LocalServer\scripts\WinScripts\StopServer.ps1
```

**Linux:**
```bash
./LocalServer/scripts/LinuxScripts/StopServer.sh
```

### 4. Wichtige URLs

| URL                              | Beschreibung          |
|----------------------------------|-----------------------|
| `http://127.0.0.1:8765/`        | Root                  |
| `http://127.0.0.1:8765/docs`    | Swagger UI            |
| `http://127.0.0.1:8765/health`  | Health / Monitoring   |

---

## Desktop App – Development

```powershell
cd PyScrapperDesktopApp
dotnet restore
dotnet build
dotnet run
```

Oder direkt über **JetBrains Rider** oder **Visual Studio**.

### NuGet-Pakete installieren (Skript)

**Windows:**
```powershell
.\LocalServer\scripts\WinScripts\InstallRequirementsFrontend.ps1
```

**Linux:**
```bash
./LocalServer/scripts/LinuxScripts/InstallRequirementsFrontend.sh
```

Das Skript prüft, welche Pakete bereits vorhanden sind, und installiert nur fehlende.

### Build-Ausgabe (kompilierte `.exe`)

```
PyScrapperDesktopApp\bin\Debug\net9.0\PyScrapperDesktopApp.exe      # Debug
PyScrapperDesktopApp\bin\Release\net9.0\PyScrapperDesktopApp.exe    # Release
```

Release-Build:

```powershell
dotnet publish -c Release
```

---

## Web Interface – Development

Das Web-Frontend ist eine **React / TypeScript**-Applikation, die via **Vite** gebaut wird und über den Browser auf den LocalServer zugreift.

### Voraussetzungen

- Node.js (aktuell)
- npm

### Setup & Start

```bash
cd PyScrapperWebInterface
npm install
npm run dev
```

Die App läuft dann standardmäßig auf `http://localhost:5173` und kommuniziert mit dem LocalServer auf `http://127.0.0.1:8765`.

### Build

```bash
npm run build
```

---

## Tests – Desktop App

Unit Tests für die Desktop App befinden sich in `PyScrapperDesktopApp.Tests/`.

```powershell
cd PyScrapperDesktopApp.Tests
dotnet test
```

---

## Bekannte Stolperfallen

- Die Desktop-App **startet den LocalServer automatisch** beim App-Start. Ein manueller Server-Start ist nicht notwendig.
- **FFmpeg** wird für YouTube-Downloads benötigt und muss im PATH liegen. Das jeweilige `StartServer`-Skript installiert es automatisch.
- **Playwright** wird für Seiten mit Bot-Schutz (z.B. Bandcamp) als Fallback-Browser benötigt. Nach Installation der Python-Abhängigkeiten einmalig `playwright install` ausführen.
- **LibVLC / VideoLAN.LibVLC.Windows** muss für den integrierten Medienplayer vorhanden sein – wird über NuGet bereitgestellt.
- `Avalonia.Diagnostics` ist nur im **Debug**-Build aktiv (bewusst so konfiguriert im `.csproj`).
- Downloads landen standardmäßig im Ordner `PyScrapper/Downloads/` (konfigurierbar per Request-Parameter `download_path`).
- Die Desktop-App persistiert heruntergeladene Medien in `data/downloadedMedias.json` – diese Datei nicht manuell löschen ohne Datenverlust.
- Der LocalServer erlaubt CORS-Anfragen von `http://localhost:5173` und `http://127.0.0.1:5173` (Web Interface Dev-Server).
