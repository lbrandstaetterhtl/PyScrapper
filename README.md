# PyScrapper – Entwickler-README

Diese Datei ist der Einstieg für Entwickler. Sie enthält nur das Nötigste: was das Projekt ist,
wie man es lokal zum Laufen bringt und wo die eigentliche Dokumentation liegt.

**Repository:** [github.com/lbrandstaetterhtl/PyScrapper](https://github.com/lbrandstaetterhtl/PyScrapper)

**Release zum Testen:** [PyscrapperInstaller v1.0.1](https://github.com/lbrandstaetterhtl/PyscrapperInstaller/releases/tag/v1.0.1)

---

## Dokumentation

Die vollständige technische Dokumentation liegt als HTML im Ordner **`HTML_Doku/`**.
Jede Datei ist eigenständig, ohne Abhängigkeiten — einfach im Browser öffnen.

| Datei | Inhalt |
|---|---|
| `HTML_Doku/PythonModule-Doku.html` | Engine: Provider, Downloadverfahren (FILE/HLS/UMP), Datenmodelle, Validierung |
| `HTML_Doku/LocalServer-Doku.html` | Backend: alle HTTP-Endpunkte, SQLite-Schema, Betrieb und Tests |
| `HTML_Doku/PyScrapperDesktopApp-Doku.html` | Desktop-Client: Schichten, Abläufe, Fenster, Serveraufrufe |

Jede Doku enthält Volltextsuche (`/` oder `Strg+K`), einen Dateibaum, Signaturen mit Parametern
und Defaults sowie den kompletten Quelltext mit verlinkbaren Zeilennummern. Sie wird direkt aus
dem Code erzeugt und ist damit immer auf dem Stand der Dateien, aus denen sie gebaut wurde.

**In dieser README nachschlagen:** Setup, Ports, Start. **Alles andere:** in der HTML-Doku.

---

## Was das Projekt ist

Ein lokales Werkzeug zum Suchen, Herunterladen und Abspielen von Medien. Vier Komponenten:

| Ordner | Was | Technik |
|---|---|---|
| `PythonModule/` | Engine — Provider, Downloader, Datenmodelle | Python |
| `LocalServer/` | HTTP-Schicht über der Engine, SQLite | FastAPI, Uvicorn |
| `PyScrapperDesktopApp/` | Windows-Client | Avalonia 11, .NET 9 |
| `PyScrapperWebInterface/` | Experimentelles Web-Frontend | React, TypeScript, Vite |

Der Server hört standardmäßig auf **`http://127.0.0.1:8765`**. Desktop-App und Web-Frontend
sprechen ausschließlich über HTTP mit ihm; eigene Datenhaltung gibt es auf Clientseite nicht.

---

## Lokal starten

Reihenfolge ist wichtig: **erst der Server**, dann die Clients.

### 1. Server

```powershell
Set-Location .\LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Alternativ `.\scripts\startServer.ps1` — das Skript nimmt das venv im Serverordner, falls vorhanden.

Vor dem ersten Start braucht es eine `.env` in `LocalServer/` mit einem `ADMIN_KEY`:

```text
ADMIN_KEY=<beliebiger zufälliger Wert>
```

Fast alle Endpunkte verlangen diesen Wert im Header `X-Admin-Key`. Der Server-Installer erzeugt
ihn automatisch.

### 2. Desktop-App

```powershell
Set-Location .\PyScrapperDesktopApp
dotnet restore
dotnet run
```

Beim ersten Start legt die App `data/config.json` an. Dort werden Serveradresse, Port und der
API-Schlüssel hinterlegt — bearbeitbar im Fenster *Config bearbeiten*. Der Schlüssel wird per
Windows-DPAPI verschlüsselt gespeichert.

Ohne laufenden Server bricht der Launcher ab.

### 3. Web-Frontend

```powershell
Set-Location .\PyScrapperWebInterface
npm install
npm run dev
```

---

## Voraussetzungen

| Was | Wofür |
|---|---|
| Python 3.12 | Server und Engine |
| .NET SDK 9.0 | Desktop-App |
| Node 20+ | Web-Frontend |
| ffmpeg / ffprobe | Codec-Prüfung und Konvertierung |
| Playwright Chromium | Provider, die auf Browser-Sniffing angewiesen sind |
| Windows | DPAPI, LibVLC-Cache und VC++-Redistributable sind Windows-spezifisch |

---

## Installer

VERALTETE VERSIONEN!!!!
Im Repository liegen zwei Inno-Setup-Skripte, aber keine fertigen EXEs. Beide installieren pro
Benutzer nach `%LOCALAPPDATA%\Programs\` und brauchen keine Adminrechte.

| Skript | Installiert | Zielordner |
|---|---|---|
| `desktop-installer.iss` | Client, .NET-Runtime, VC++, ffmpeg | `…\Programs\PyScrapper` |
| `server-installer.iss` | Backend, eigenes Python, ffmpeg, Chromium, `.env` mit generiertem Key | `…\Programs\PyScrapperServer` |

Bauen (Inno Setup 6.1+ vorausgesetzt):

```powershell
dotnet publish PyScrapperDesktopApp -c Release --self-contained false
ISCC.exe server-installer.iss
ISCC.exe desktop-installer.iss
```

Vorher in beiden `.iss` die Pfad-Defines auf den eigenen Klon-Ort anpassen
(`MyAppPublishDir` bzw. `ProjectRoot`). Für den Desktop-Installer immer den `publish\`-Ordner
einpacken, nie den rohen Build-Ordner. Die Setups landen in `installer-output\`.

Installiert wird **erst der Server, dann die Desktop-App**.

---

## Wichtige Pfade

| Pfad | Zweck |
|---|---|
| `LocalServer/.env` | `ADMIN_KEY` |
| `LocalServer/Data/data.db` | SQLite-Datenbank, entsteht beim ersten Start |
| `LocalServer/logs/server_runtime.log` | Server-Log |
| `PyScrapperDesktopApp/data/config.json` | Serveradresse, Port, verschlüsselter Schlüssel |
| `PyScrapperDesktopApp/logs/app.log` | App-Log |
| `HTML_Doku/` | Technische Dokumentation |

---

## Gut zu wissen

- Der Server ist für den lokalen Betrieb gedacht und nicht für öffentliches Hosting ausgelegt.
- Die Desktop-App startet den Server nicht selbst — er muss vorher laufen.
- Das Web-Frontend ist experimentell; die Fetch-URLs sind fest verdrahtet und müssen ggf. auf den
  Serverport angepasst werden.
- Die Desktop-App leitet ihre Pfade aus dem Arbeitsverzeichnis ab und erwartet in der IDE den
  Ausführungspfad `bin/Debug/net9.0` innerhalb der Repository-Struktur.

---

## Schnellkommandos

```powershell
# Server-Health
Invoke-RestMethod http://127.0.0.1:8765/health -Headers @{ "X-Admin-Key" = "<key>" }

# OpenAPI-Oberfläche
Start-Process http://127.0.0.1:8765/docs

# Logs mitlesen
Get-Content .\LocalServer\logs\server_runtime.log -Tail 100 -Wait
Get-Content .\PyScrapperDesktopApp\logs\app.log -Tail 100 -Wait
```
