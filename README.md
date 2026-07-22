# PyScrapper

PyScrapper is a local-first media scraping and download toolkit with three primary components:

- **Backend API** (`LocalServer`) built with **FastAPI** (Python)
- **Desktop client** (`PyScrapperDesktopApp`) built with **C# / Avalonia / .NET 9**
- **Web client** (`PyScrapperWebInterface`) built with **React / TypeScript / Vite**

It provides a unified workflow for searching media, starting downloads, tracking progress, and managing downloaded content locally.

---

## Table of Contents

- [Project Goals](#project-goals)
- [Current Architecture](#current-architecture)
- [Repository Structure](#repository-structure)
- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [API Overview](#api-overview)
- [Data Storage & Database Management](#data-storage--database-management)
- [Operational Notes](#operational-notes)
- [Troubleshooting](#troubleshooting)
- [Development Notes](#development-notes)
- [Security Scope](#security-scope)
- [License](#license)

---

## Project Goals

- Offer a **local-first** media workflow (search → download → manage → play).
- Keep scraping/provider logic reusable through a dedicated Python core module.
- Support multiple frontends (desktop + web) against one local backend API.
- Maintain practical diagnostics (`/health`, runtime logs) for local operation.

---

## Current Architecture

### 1) `LocalServer` (FastAPI)

Local API server running on `127.0.0.1:8765`.

Responsibilities:

- Accept search/download/command requests
- Queue and process tasks asynchronously
- Report task progress and server health
- Write runtime logs

### 2) `PythonModule`

Reusable scraping core and service layer.

Responsibilities:

- Provider-specific integrations
- Shared HTTP/session utilities
- Fallback browser handling via Playwright
- Server-side processors for command/search/download

### 3) `PyScrapperDesktopApp` (Avalonia)

Cross-platform desktop UI consuming the local API.

Responsibilities:

- Search and download UX
- Playlist/media management
- Playback (LibVLCSharp)
- Health/log visualization
- Conversion workflows

### 4) `PyScrapperWebInterface` (React + Vite)

Browser-based UI consuming the same local API.

Responsibilities:

- Web search/download interaction
- Local backend connectivity during development

---

## Repository Structure

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

## Core Features

- Multi-provider search (current providers include `suno`, `youtube`, `archive`, `bandcamp`)
- Download task creation and progress tracking
- Queue-based backend request processing
- Desktop media list persistence
- Playlist and playback support
- Optional codec/conversion workflows
- Health endpoint and runtime log visibility

---

## Technology Stack

### Backend

- Python 3.10+
- FastAPI + Uvicorn
- Pydantic
- yt-dlp
- Playwright

### Desktop

- .NET 9
- Avalonia 11.3.8
- LibVLCSharp

### Web

- React
- TypeScript
- Vite

---

## Requirements

### Core Tools

- **Git**
- **Python 3.10+**
- **.NET SDK 9.0**
- **Node.js + npm**
- **FFmpeg** (required for selected download/conversion flows)

### Python Dependencies

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

## Quick Start

### 1) Start LocalServer

#### Windows (PowerShell)

```powershell
cd LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

#### Linux / macOS (Bash)

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

Stop with `Ctrl+C`.

---

### 2) Run Desktop App

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

### 3) Run Web Interface

```bash
cd PyScrapperWebInterface
npm install
npm run dev
```

Default dev URL: `http://localhost:5173`

---

## API Overview

Main local endpoints:

- `GET /` – service root
- `GET /health` – uptime, memory, PID, active Python processes
- `POST /command` – queue command events (e.g. `quit`)
- `POST /search` – provider search
- `POST /download` – create download task
- `GET /download/progress/{task_id}` – fetch task progress

Notes:

- Request processing is queue-based.
- Concurrency is limited with `asyncio.Semaphore(50)`.

---

## Data Storage & Database Management

PyScrapper currently follows a **hybrid persistence approach**:

1. **JSON persistence** (desktop-visible state), currently including:
   - `PyScrapperDesktopApp/data/downloadedMedias.json`
2. **Runtime/log-based backend state** in `LocalServer`
3. **Documented SQLite-oriented architecture concepts** in desktop technical docs (`PyScrapperDesktopApp/Doku`)

### Current Practical Behavior

- Downloaded media metadata is persisted in JSON for desktop usage.
- Server runtime behavior is traceable via log output.
- Database concepts are documented but not yet enforced as a single runtime source everywhere.

### Recommended Evolution Path

To standardize long-term data management:

1. Introduce a single DB access layer (repository/service pattern).
2. Define schema versions and migration scripts.
3. Add startup integrity checks + safe recovery paths.
4. Support import/export between JSON and SQLite.
5. Add backup/restore workflow for local user data.

---

## Operational Notes

- Ensure **FFmpeg** is available in `PATH` for YouTube/conversion workflows.
- For Playwright fallback browser support, run once after installing dependencies:

```bash
playwright install
```

- CORS is configured for local web development origins (`localhost:5173`, `127.0.0.1:5173`).
- Default media output folder: `PyScrapper/Downloads/` (can be overridden via `download_path` in request payload).

---

## Troubleshooting

### Server does not start

- Verify Python version (`3.10+`)
- Recreate virtual environment
- Reinstall requirements

### Web UI cannot reach backend

- Confirm LocalServer is running on `127.0.0.1:8765`
- Check browser console/network errors
- Verify CORS/dev URL is unchanged

### Downloads fail for provider content

- Update `yt-dlp`
- Ensure FFmpeg is installed and available
- Run `playwright install` if fallback browser paths are used

### Desktop playback issues

- Check LibVLC runtime availability on your platform
- Validate file paths of downloaded media

---

## Development Notes

- This repository recently converged into a cleaner architecture with explicit LocalServer + PythonModule separation.
- Legacy startup/install scripts were removed; manual, explicit setup is now the default.
- Keep API contracts stable between backend, desktop app, and web UI to reduce integration regressions.

---

## Security Scope

PyScrapper is designed for **local development/use** and is **not hardened for public internet deployment** in its current form.

---

## License

No license file is currently defined in this repository.
