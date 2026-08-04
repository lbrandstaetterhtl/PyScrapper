# PyScrapper – Projektstatistik

> Repo: `github.com/lbrandstaetterhtl/PyScrapper` · Verifiziert: 2026-08-04

> Gezählt ohne Build-/Cache-/Vendor-Verzeichnisse wie `bin/`, `obj/`, `.venv/`, `node_modules/`, `logs/`, `Data/`, `data/` und `__pycache__/`.

---

## Repository

- **280 Commits** über **63 aktive Tage** (`2026-02-25` → `2026-08-04`)
- Bester Tag: `2026-02-25` mit **27 Commits**
- **1 lokaler Branch** · **0 Tags/Releases**
- **5 normalisierte Autor-E-Mails** im Git-Verlauf; die Leon-Commits sind auf mehrere Aliasse verteilt

---

## Codebase – 18.149 Zeilen · 130 Quelltextdateien · 8 Dateitypen

| Typ | Dateien | Zeilen | Anteil |
|---|---:|---:|---:|
| Python | 41 | 7.532 | 41,5 % |
| C# | 46 | 7.105 | 39,1 % |
| AXAML | 20 | 1.872 | 10,3 % |
| Inno Setup | 2 | 634 | 3,5 % |
| TypeScript/TSX | 14 | 709 | 3,9 % |
| CSS | 6 | 267 | 1,5 % |
| PowerShell | 1 | 30 | 0,2 % |

**5 größte Quelltextdateien:** `LocalServer/server.py` (1.154) · `PythonModule/core/request/EmergencyBrowser.py` (1.097) · `LocalServer/serverBak.py` (1.024) · `PyScrapperDesktopApp/ViewModels/LauncherWindowViewModel.cs` (702) · `PythonModule/core/download/HLS.py` (639)

**3 kleinste Quelltextdateien:** `PythonModule/models/__init__.py` (0) · `PythonModule/serverservices/__init__.py` (0) · `PythonModule/__init__.py` (1)

---

## Architektur

| Layer | Zeilen | Anteil |
|---|---:|---:|
| Frontend (C# + AXAML + Web-UI: CSS/TS/TSX) | 9.953 | 54,8 % |
| Backend (Python) | 7.532 | 41,5 % |
| DevOps / Installer (PowerShell + Inno Setup) | 664 | 3,7 % |

### C# Desktop App — Avalonia · .NET 9 · MVVM

- **15 ViewModels** · **18 Views** · **11 Models**
- **53** `[RelayCommand]` · **78** `[ObservableProperty]` · **61** `async Task`-Methoden
- kein klassischer DI-Container gefunden (`ServiceCollection` / `DependencyInjection` fehlen)

### Python Backend — FastAPI

- **41 Python-Quelltextdateien** in `PythonModule/` plus `LocalServer/server.py` und `LocalServer/serverBak.py`
- **17 Custom-Exception-Klassen**
- **21 Request/Response-/Model-Klassen**
- **105 Funktionen**, davon **9 async**

### API-Endpunkte

- Aktiver Server `LocalServer/server.py`: **33 Routen**
- Legacy-Server `LocalServer/serverBak.py`: **32 Routen**

Wesentliche Endpunkte im aktiven Server:

| Methode | Route |
|---|---|
| GET | `/` |
| POST | `/command` |
| POST | `/download` |
| GET | `/download/progress/{task_id}` |
| POST | `/search` |
| GET | `/health` |
| POST | `/save` |
| POST | `/set/user/loggedIn` |
| POST | `/set/user/lastLoggedIn` |
| GET | `/get/user/{identifier}` |
| GET | `/getall/users` |
| POST | `/create-tables/` |
| POST | `/create/user/` |
| POST | `/delete/user/{identifier}` |
| GET | `/get/playlists/{identifier}` |
| POST | `/create/playlist/` |
| POST | `/delete/playlist/{identifier}` |
| GET | `/getall/playlists` |
| POST | `/create/downloadedmedia` |
| POST | `/delete/downloadedmedia/{identifier}` |
| GET | `/get/downloadedmedia/{identifier}` |
| GET | `/getuser/downloadedmedias/{user_identifier}` |
| POST | `/create/settings/` |
| POST | `/delete/settings/{identifier}` |
| GET | `/get/settings/{user_identifier}` |
| GET | `/getall/settings` |
| POST | `/create/playlistmedia` |
| POST | `/delete/playlistmedia` |
| GET | `/get/playlistmedias/{playlist_identifier}` |
| GET | `/getuser/playlists/{user_identifier}` |
| POST | `/login` |
| POST | `/register` |
| POST | `/logout/{identifier}` |

### Provider Support

| Provider | Download | Search | Hinweis |
|---|---|---|---|
| Archive | ✅ | ✅ | `.mp3`, `.mp4`, `.wav`, `.mkv` |
| Bandcamp | ✅ | ✅ | `.mp3` |
| YouTube | ✅ | ✅ | `.mp3`, `.mp4` |
| Suno | ✅ | ❌ | zentral nur `.mp3` / `.mp4` |
| Soundcloud | ✅ | ❌ | Download-only |
| Default | ✅ | ❌ | Download-only |

`ProviderTypes` enthält zusätzlich `Wcoflix` und `Aniworld`, aber diese beiden Provider sind derzeit nicht in den Provider-Mappings verdrahtet.

---

## Dependencies

- **NuGet:** 13 Package-References in `PyScrapperDesktopApp.csproj`
  - Avalonia 11.3.8 (5 Referenzen)
  - CommunityToolkit.Mvvm 8.4.0
  - DotNetEnv 3.2.0
  - FluentAvaloniaUI 2.0.5
  - LibVLCSharp 3.9.6
  - LibVLCSharp.Avalonia 3.9.6
  - Microsoft.Data.Sqlite 10.0.5
  - System.Security.Cryptography.ProtectedData 10.0.10
  - VideoLAN.LibVLC.Windows 3.0.23
- **pip:** 8 Einträge in `LocalServer/requirements.txt`
  - `fastapi`, `uvicorn[standard]`, `pydantic`, `certifi`, `yt-dlp`, `playwright`, `bcrypt`, `dotenv`
- **npm:** 2 Runtime-Dependencies + 12 Dev-Dependencies in `PyScrapperWebInterface/package.json`
  - Runtime: `react`, `react-dom`
  - Tooling: Vite, TypeScript, ESLint und React-Plugin-Stack

---

## Praktiken / Qualität

| Aspekt | Status |
|---|---|
| MVVM | ✅ |
| Async/Await (C# & Python) | ✅ |
| Source Generators (CommunityToolkit) | ✅ |
| Custom Exception Hierarchy | ✅ 17 Klassen |
| Logging | ✅ |
| Klassische Dependency Injection | ❌ |
| Formale Unit-Tests | ❌ |
| CI/CD | ❌ |

- Es gibt Python-Testskripte in `LocalServer/tests/`, aber kein formales Test-Framework-Projekt mit z. B. `pytest`/xUnit-Testfällen.
- Das Web-Frontend adressiert `http://127.0.0.1:8000`, während `LocalServer/scripts/startServer.ps1` den Server auf Port `8765` startet; das ist ein echter Integrations-Hinweis.
- `LocalServer/server.py` schützt auch `/login` mit `require_admin`.

---

## Verifikation

Diese Statistik wurde direkt gegen den Workspace geprüft mit:

- Git-Historie (`git log`, `git rev-list`)
- Quelltext-Suche in `LocalServer/server.py` und `LocalServer/serverBak.py`
- Abhängigkeitsdateien: `LocalServer/requirements.txt`, `PyScrapperDesktopApp/PyScrapperDesktopApp.csproj`, `PyScrapperWebInterface/package.json`
- Struktur- und Zählprüfungen für `PyScrapperDesktopApp/`, `PyScrapperWebInterface/src/`, `PythonModule/` und `LocalServer/tests/`

