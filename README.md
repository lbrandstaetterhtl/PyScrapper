# PyScrapper

PyScrapper is a local-first media scraping and download toolkit with three main parts:

- **Python FastAPI backend** (`LocalServer` + `PythonModule`)
- **Cross-platform desktop app** (**C# / Avalonia / .NET 9**)
- **Web interface** (**React / TypeScript / Vite**)

It helps you search and download media from supported providers, monitor download progress, and manage downloaded media locally.

---

## What’s new (latest project state)

- Unified architecture with a dedicated **LocalServer** and reusable **PythonModule** core.
- Expanded desktop workflow with windows for search/download, health, logs, playlists, media playback, and codec conversion.
- Included **web frontend** (`PyScrapperWebInterface`) for browser-based interaction with the local backend.
- Runtime and diagnostics via server logging (`LocalServer/logs/server_runtime.log`) and `/health` endpoint.
- Current stack includes **.NET 9**, **Avalonia 11.3.8**, **LibVLCSharp**, **FastAPI**, **yt-dlp**, and **Playwright**.
- ✅ **No startup/install scripts required anymore** (script directory removed).

---

## Repository structure

```text
PyScrapper/
├── LocalServer/                  # FastAPI backend (Python)
│   ├── server.py
│   ├── requirements.txt
│   └── logs/
│
├── PythonModule/                 # Core scraping/search/download logic
│   ├── Session.py
│   ├── core.py
│   ├── emergencyBrowser.py
│   ├── models/
│   ├── providers/
│   └── serverservices/
│
├── PyScrapperDesktopApp/         # Desktop app (C# / Avalonia / .NET 9)
├── PyScrapperDesktopApp.Tests/   # Desktop unit tests
├── PyScrapperWebInterface/       # React/TypeScript web UI
├── Downloads/                    # Default media output folder
└── Notes/                        # Project notes and stats
```

---

## Architecture overview

### 1) LocalServer (FastAPI)

Local API server on `127.0.0.1:8765`.

Main endpoints:

- `GET /` – service root
- `GET /health` – uptime, memory, PID, running Python processes
- `POST /command` – queued commands (e.g. `quit`)
- `POST /download` – create download task
- `GET /download/progress/{task_id}` – task progress
- `POST /search` – provider search

Technical notes:

- Request handling is queue-based (`asyncio` queues).
- Concurrency is controlled with `asyncio.Semaphore(50)`.
- Server runtime logs are written to `LocalServer/logs/server_runtime.log`.
- Designed for **local use**, not hardened for public internet deployment.

Supported providers (current):

- `suno`, `suno.com`
- `youtube`, `youtube.com`
- `archive`, `archive.org`
- `bandcamp`

### 2) PythonModule

Reusable backend core with provider integrations and server processors.

Key modules:

- `Session.py` – shared HTTP session management
- `core.py` – HTTP helper utilities
- `emergencyBrowser.py` – Playwright fallback for protected pages
- `providers/` – provider-specific implementations
- `serverservices/` – server-side processors for command/search/download

### 3) Desktop App (Avalonia)

The desktop client communicates with LocalServer over HTTP and includes:

- Search and download workflows
- Downloaded media list and persistence
- Media playback via **LibVLCSharp**
- Playlist creation and management
- Codec conversion
- Health and logs views

Persistent app data is stored in:

- `PyScrapperDesktopApp/data/downloadedMedias.json`

### 4) Web Interface (React + Vite)

A browser UI for interacting with the same local backend (`127.0.0.1:8765`).

### 5) Datenbank-Management

PyScrapper nutzt aktuell eine **hybride Persistenzstrategie**:

- **JSON-basierte Persistenz** in der Desktop-App (z. B. `downloadedMedias.json`)
- **In-memory/Datei-orientierte Laufzeitdaten** im LocalServer
- **SQLite-Bezug in der technischen Desktop-Dokumentation** (`PyScrapperDesktopApp/Doku`)

#### Zuständigkeiten

- Speicherung und Wiederherstellung heruntergeladener Medien
- Verwaltung von Playlists und app-spezifischen Zuständen
- Grundlage für zukünftige, konsistente DB-Migrationen

#### Aktueller Stand

- Primärer sichtbarer Persistenzpfad im Code: `PyScrapperDesktopApp/data/downloadedMedias.json`
- Erweiterte DB-Konzepte sind in der Desktop-Dokumentation beschrieben
- Für produktive DB-Szenarien (Backups, Migration, Integritätsprüfungen) wird empfohlen,
  ein einheitliches SQLite-Schema als Single Source of Truth zu etablieren

#### Empfehlungen für den Ausbau

1. Einheitliche Datenzugriffsschicht (Repository/Service Layer)
2. Versionierte Migrationen (z. B. mit klaren Schema-Versionen)
3. Validierung + Integrity Checks beim Start
4. Optionaler Export/Import für JSON ↔ SQLite
5. Regelmäßige Backup-Strategie für lokale Nutzerdaten

---

## Requirements

### Core

- **Git**
- **Python 3.10+**
- **.NET SDK 9.0**
- **Node.js + npm** (for web interface)
- **FFmpeg** (required for some download/conversion workflows)

### Python dependencies

Defined in `LocalServer/requirements.txt`:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `certifi`
- `yt-dlp`
- `playwright`
- `bcrypt`
- `dotenv`

---

## Quick start (scriptless)

## 1) Start LocalServer

### Windows (PowerShell)

```powershell
cd LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

### Linux / macOS (Bash)

```bash
cd LocalServer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Server URLs:

- `http://127.0.0.1:8765/`
- `http://127.0.0.1:8765/docs`
- `http://127.0.0.1:8765/health`

To stop the server, press `Ctrl+C` in the terminal.

---

## 2) Run Desktop App

```powershell
cd PyScrapperDesktopApp
dotnet restore
dotnet build
dotnet run
```

Optional tests:

```powershell
cd ../PyScrapperDesktopApp.Tests
dotnet test
```

---

## 3) Run Web Interface

```bash
cd PyScrapperWebInterface
npm install
npm run dev
```

Default dev URL: `http://localhost:5173`

---

## Operational notes

- FFmpeg must be available in PATH for YouTube and conversion-related operations.
- For Playwright-based fallback browser support, run once after dependency install:

```bash
playwright install
```

- CORS is configured for local web dev origins (`localhost:5173` / `127.0.0.1:5173`).
- Default media output folder: `PyScrapper/Downloads/` (overridable via request parameter `download_path`).

---

## Security and scope

PyScrapper is intended for **local development/use**. The current LocalServer setup is not hardened for public deployment.

---

## License

No license file is currently defined in this repository.
