# PyScrapper

PyScrapper is a local-first media scraping and download toolkit with three main parts:

- **Python FastAPI backend** (`LocalServer` + `PythonModule`)
- **Cross-platform desktop app** (**C# / Avalonia / .NET 9**)
- **Web interface** (**React / TypeScript / Vite**)

It helps you search and download media from supported providers, monitor download progress, and manage your downloaded media locally.

---

## What’s new (latest project state)

- Unified architecture with a dedicated **LocalServer** and reusable **PythonModule** core.
- Expanded desktop workflow with dedicated windows for search/download, health, logs, playlists, media playback, and codec conversion.
- Added/maintained **web frontend** (`PyScrapperWebInterface`) for browser-based interaction with the local backend.
- Runtime and diagnostics improvements via server logging (`LocalServer/logs/server_runtime.log`) and `/health` endpoint.
- Current tested stack includes **.NET 9**, **Avalonia 11.3.8**, **LibVLCSharp**, **FastAPI**, **yt-dlp**, and **Playwright**.

---

## Repository structure

```text
PyScrapper/
├── LocalServer/                  # FastAPI backend (Python)
│   ├── server.py
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── WinScripts/
│   │   └── LinuxScripts/
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

---

## Requirements

### Core

- **Git**
- **Python 3.10+**
- **.NET SDK 9.0**
- **Node.js + npm** (for web interface)
- **FFmpeg** (required for some download/conversion workflows)

### Python dependencies

Defined in `LocalServer/requirements.txt`, including:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `certifi`
- `yt-dlp`
- `playwright`

---

## Quick start

## 1) Start LocalServer

### Windows (PowerShell)

```powershell
.\LocalServer\scripts\WinScripts\StartServer.ps1
```

### Linux (Bash)

```bash
./LocalServer/scripts/LinuxScripts/StartServer.sh
```

This script-based start is recommended because it handles virtual environment setup, missing dependencies, and runtime preparation.

Server URLs:

- `http://127.0.0.1:8765/`
- `http://127.0.0.1:8765/docs`
- `http://127.0.0.1:8765/health`

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

- The desktop app can auto-start the LocalServer on launch (depending on current app flow/config).
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

If you plan to distribute PyScrapper, add a `LICENSE` file and update this section accordingly.
