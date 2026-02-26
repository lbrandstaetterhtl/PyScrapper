# PyScrapper – Developer README

Diese Datei richtet sich **ausschließlich an Entwickler**.  
Sie beschreibt Architektur, Setup, typische Workflows und bekannte Stolperfallen.

---

## Projektstruktur (High Level)

```
PyScrapper/
├── LocalServer/ # FastAPI Backend (Python)
│ ├── server.py # Einstiegspunkt (uvicorn app)
│ ├── scripts/ # Start-/Helper-Skripte (z.B. StartServer.ps1)
│ └── .venv/ # Virtuelle Umgebung (lokal)
│
├── PythonModule/ # Core-Logik (Sessions, Scraping, Downloads)
│ ├── Session/
│ ├── Suno/
│ └── ...
│
├── PyScrapperDesktopApp/ # Desktop Client (.NET / C#)
│ ├── *.sln
│ └── ...
│
└── README.md
```


---

## Architektur-Überblick

### LocalServer (Python / FastAPI)

- Läuft lokal via **uvicorn**
- Stellt HTTP-Endpunkte bereit:
  - `/command` → Queue-basierte Commands
  - `/download` → Download-Jobs
  - `/health` → Status / Monitoring
- Nutzt **asyncio Queues**, um Requests von der Verarbeitung zu entkoppeln
- Importiert Logik aus `PythonModule`

**Wichtig:**  
Der Server ist nicht gehärtet und **nicht für öffentliches Deployment gedacht**.

---

### PythonModule

- Enthält die eigentliche Business-Logik
- Kein Web-Code
- Wird direkt vom LocalServer importiert
- Kann unabhängig getestet/erweitert werden

Empfehlung:
- Keine Side-Effects beim Import
- Keine globalen Netzwerk-Calls
- Exceptions sauber nach oben werfen

---

### Desktop App (C# / .NET)

- Client für den LocalServer
- Kommuniziert über HTTP
- Erwartet einen laufenden Server auf `127.0.0.1:8765`
- Kann separat gebaut und gestartet werden

---

## Entwicklungs-Setup

### Voraussetzungen

- Python **3.10+**
- Git
- .NET SDK **6 oder neuer**
- (Windows empfohlen für aktuelle Scripts)

---

## LocalServer – Setup

### 1. Virtuelle Umgebung

Windows (PowerShell):
```
cd LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS:

```
cd LocalServer
python3 -m venv .venv
source .venv/bin/activate
2. Dependencies installieren
pip install -r requirements.txt

Falls keine requirements.txt vorhanden ist:

pip install fastapi uvicorn pydantic

Zusätzliche Dependencies ergeben sich aus PythonModule.
ModuleNotFoundError = fehlendes Paket.
```

3. Server starten

Direkt:

```
uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765
```

Oder über Script:

```
.\scripts\StartServer.ps1
```

4. Wichtige URLs

Swagger UI:
```
http://127.0.0.1:8765/docs
```

Health Endpoint:
```
http://127.0.0.1:8765/health
```

Desktop App – Development

```
cd PyScrapperDesktopApp
dotnet restore
dotnet build
dotnet run
```

Oder über Rider / Visual Studio.
