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
│   ├── scripts/                  # PowerShell-Skripte (Start, Stop, Install, ...)
│   │   ├── StartServer.ps1
│   │   ├── StopServer.ps1
│   │   ├── InstallRequirementsBackend.ps1
│   │   ├── InstallRequirementsFrontend.ps1
│   │   ├── InstallFFMPEG.ps1
│   │   └── ActivateVirtualEnvironment.ps1
│   ├── logs/                     # Runtime-Logs des Servers
│   └── .venv/                    # Virtuelle Umgebung (lokal, nicht eingecheckt)
│
├── PythonModule/                 # Core-Logik (Sessions, Scraping, Downloads)
│   ├── Session.py
│   ├── Suno.py
│   └── Youtube.py
│
├── PyScrapperDesktopApp/         # Desktop Client (C# / Avalonia / .NET 9)
│   ├── *.sln / *.csproj
│   ├── Models/                   # ApiClient, AppData, AppLogger, AudioPlayer
│   ├── ViewModels/               # MVVM ViewModels (Main, Suno, Youtube, MediaPlayer, ...)
│   ├── Views/                    # Avalonia AXAML Windows
│   └── data/                     # Persistente App-Daten (downloadedMedias.json)
│
├── Downloads/                    # Standard-Downloadordner für Medien
└── Notes/                        # Projektnotizen & Statistiken
```

---

## Architektur-Überblick

### LocalServer (Python / FastAPI)

- Läuft lokal via **uvicorn**
- Stellt folgende HTTP-Endpunkte bereit:

| Methode | Pfad        | Beschreibung                                      |
|---------|-------------|---------------------------------------------------|
| GET     | `/`         | Root – Startbestätigung                           |
| GET     | `/health`   | Uptime, RAM-Verbrauch, PID, laufende Python-Prozesse |
| POST    | `/command`  | Queue-basierte Kommandos (z.B. `quit`)            |
| POST    | `/download` | Download-Job für einen URL (Suno oder YouTube)    |
| POST    | `/search`   | YouTube-Suche mit konfigurierbarer Trefferanzahl  |

- Nutzt **asyncio Queues**, um Requests von der Verarbeitung zu entkoppeln
- Parallele Downloads durch `asyncio.Semaphore(50)` begrenzt
- Runtime-Logs werden in `LocalServer/logs/server_runtime.log` geschrieben
- Importiert Logik aus `PythonModule`

**Unterstützte Provider:** `suno`, `suno.com`, `youtube`, `youtube.com`

**Wichtig:**  
Der Server ist nicht gehärtet und **nicht für öffentliches Deployment gedacht**.

---

### PythonModule

- Enthält die eigentliche Business-Logik
- Kein Web-Code – wird direkt vom LocalServer importiert
- Module:
  - `Session.py` – gemeinsame HTTP-Session (Cookies etc.)
  - `Suno.py` – Download von suno.com
  - `Youtube.py` – Download (Audio/Video) und Suche via `yt-dlp`
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
  - `YoutubeScrapWindow` – YouTube-Suche & Download (mp3/mp4)
  - `MediaPlayerWindow` – integrierter Medienplayer
  - `InputWindow` – generisches Eingabedialog-Fenster
  - `MassageBox` – benutzerdefinierte Message-Box
- **Medien-Wiedergabe** via **LibVLCSharp** (Audio & Video)
- Heruntergeladene Medien werden in `data/downloadedMedias.json` persistiert

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

---

## Entwicklungs-Setup

### Voraussetzungen

- Python **3.10+**
- Git
- .NET SDK **9.0**
- FFmpeg (wird automatisch via `InstallFFMPEG.ps1` installiert, falls nicht vorhanden)
- Windows (PowerShell-Skripte sind Windows-only)

---

## LocalServer – Setup

### 1. Virtuelle Umgebung & Abhängigkeiten

Am einfachsten über das Start-Skript – es legt die `.venv` automatisch an,
aktiviert sie und installiert fehlende Pakete:

```powershell
.\LocalServer\scripts\StartServer.ps1
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
```

### 2. Server starten

Über Script (empfohlen – verwaltet venv, ffmpeg und Logging automatisch):

```powershell
.\LocalServer\scripts\StartServer.ps1
```

Direkt (wenn venv bereits aktiv):

```
uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765
```

### 3. Server stoppen

```powershell
.\LocalServer\scripts\StopServer.ps1
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

```powershell
.\LocalServer\scripts\InstallRequirementsFrontend.ps1
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

## Bekannte Stolperfallen

- Die Desktop-App **startet den LocalServer automatisch** beim App-Start. Ein manueller Server-Start ist nicht notwendig.
- **FFmpeg** wird für YouTube-Downloads benötigt und muss im PATH liegen. `StartServer.ps1` installiert es automatisch.
- **LibVLC / VideoLAN.LibVLC.Windows** muss für den integrierten Medienplayer vorhanden sein – wird über NuGet bereitgestellt.
- `Avalonia.Diagnostics` ist nur im **Debug**-Build aktiv (bewusst so konfiguriert im `.csproj`).
- Downloads landen standardmäßig im Ordner `PyScrapper/Downloads/` (konfigurierbar per Request-Parameter `download_path`).
- Die Desktop-App persistiert heruntergeladene Medien in `data/downloadedMedias.json` – diese Datei nicht manuell löschen ohne Datenverlust.
