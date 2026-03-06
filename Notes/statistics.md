# PyScrapper – Project Statistics

> Repo: `github.com/lbrandstaetterhtl/PyScrapper` · Generated: 2026-03-06

---

## Repository

- **63 commits** over **10 active days** (2026-02-25 → 2026-03-06)
- Busiest day: 2026-02-25 with 27 commits
- 3 branches · 2 merge commits · 0 tags/releases
- 2 contributors (by unique email):
  - Leon (leon / p50232 / lbrandstaetterhtl) — 53 commits
  - Flip — 10 commits

---

## Codebase – 3.482 lines · 39 files · 4 languages

| Language | Files | Lines | Share |
|---|---:|---:|---:|
| C# | 19 | 1.756 | 50,4 % |
| Python | 7 | 1.125 | 32,3 % |
| AXAML | 8 | 328 | 9,4 % |
| PowerShell | 5 | 273 | 7,8 % |

**5 largest files:** server.py (390) · ApiClient.cs (281) · Youtube.py (253) · MediaPlayerWindowViewModel.cs (234) · Suno.py (196)

**3 smallest:** ViewModelBase.cs (7) · App.axaml (11) · InputWindow.axaml.cs (15)

---

## Architecture

| Layer | Lines | Share |
|---|---:|---:|
| Frontend (C# + AXAML) | 2.084 | 59,9 % |
| Backend (Python) | 1.125 | 32,3 % |
| DevOps (PowerShell scripts) | 273 | 7,8 % |

### C# Desktop App — Avalonia · .NET 9 · MVVM

- 34 classes (20 top-level + 14 inner in ApiClient)
- 6 Views · 6 ViewModels · 4 Model files
- 18 `[RelayCommand]` · 9 `[ObservableProperty]` · 16 async methods

### Python Backend — FastAPI

- 13 classes (8 custom exceptions · 4 Pydantic models · 1 Session)
- 25 functions (excl. legacy server_OLD.py)
- Max 50 concurrent downloads (asyncio.Semaphore)

### API Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Root status |
| GET | `/health` | Uptime, memory, PIDs |
| POST | `/command` | Server commands (quit) |
| POST | `/download` | Download jobs |
| POST | `/search` | YouTube search |

### Provider Support

| Provider | Download | Search |
|---|---|---|
| YouTube | .mp3, .mp4 | ✅ |
| Suno | .mp3, .mp4, .wav | ❌ |

---

## Dependencies

**NuGet (8 packages):** Avalonia 11.3.8 (5 packages) · CommunityToolkit.Mvvm 8.4.0 · FluentAvaloniaUI 2.0.5 · LibVLCSharp 3.9.6 · VideoLAN.LibVLC.Windows 3.0.23

**pip (5 packages):** fastapi · uvicorn[standard] · pydantic · certifi · yt-dlp

---

## Practices

| | Status |
|---|---|
| MVVM | ✅ |
| Async/Await (C# & Python) | ✅ |
| Source generators (CommunityToolkit) | ✅ |
| Custom exception hierarchy | ✅ 8 classes |
| Logging (5 log files) | ✅ |
| Dependency injection | ❌ |
| Unit tests | ❌ |
| CI/CD | ❌ |

