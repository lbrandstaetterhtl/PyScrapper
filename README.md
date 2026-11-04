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
| `HTML_Doku/PythonModule.html` | Engine: Provider, Downloadverfahren (FILE/HLS/UMP), ffmpeg-Muxing, Datenmodelle, Validierung |
| `HTML_Doku/LocalServer.html` | Backend: alle HTTP-Endpunkte, SQLite-Schema, Betrieb und Tests |
| `HTML_Doku/PyScrapperDesktopApp.html` | Desktop-Client: Schichten, Abläufe, Fenster, Serveraufrufe |

Jede Doku enthält Volltextsuche (`/` oder `Strg+K`), einen Dateibaum, Signaturen mit Parametern
und Defaults sowie den kompletten Quelltext mit verlinkbaren Zeilennummern. Sie wird direkt aus
dem Code erzeugt und ist damit immer auf dem Stand der Dateien, aus denen sie gebaut wurde.

Neu bauen nach Codeänderungen (nur Python-Standardbibliothek nötig):

```powershell
python HTML_Doku/_generator/build_docs.py            # alle drei
python HTML_Doku/_generator/build_docs.py LocalServer # nur eine
```

Signaturen, Quelltext, Endpunktliste, DB-Schema und Kennzahlen kommen bei jedem Lauf frisch aus
dem Code. Die erklärenden Texte liegen in `HTML_Doku/_generator/content/<Paket>/` (Seiten als HTML,
Abläufe und Hinweise als JSON) und müssen bei inhaltlichen Änderungen von Hand nachgezogen werden.
Das Skript warnt, wenn ein Text auf ein Modul oder Symbol verlinkt, das es nicht mehr gibt.

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

Der Server hört lokal auf **`http://127.0.0.1:8765`**, im Docker-Container auf Port **`8000`**.
Desktop-App und Web-Frontend sprechen ausschließlich über HTTP mit ihm; eigene Datenhaltung gibt es
auf Clientseite nicht.

---

## Lokal starten

Reihenfolge ist wichtig: **erst der Server**, dann die Clients.

### 1. Server

Vor dem ersten Start braucht es eine `.env` in `LocalServer/` mit einem `ADMIN_KEY`:

```text
ADMIN_KEY=<beliebiger zufälliger Wert>
```

Der Schlüssel schützt die Admin-Routen (Header `X-Admin-Key`). Die Routen eines angemeldeten
Benutzers verlangen stattdessen `X-User-Key` plus `Auth` (Benutzer-ID); beides liefern
`/register` bzw. `/login`. Der Server-Installer erzeugt die `.env` automatisch.

#### Variante A: Docker (empfohlen)

```bash
cd LocalServer/docker
docker compose up -d --build      # danach http://localhost:8000
```

Das Image baut das Rust-Modul `ocr` gleich mit (siehe unten), installiert ffmpeg, die
Python-Abhängigkeiten und Playwright-Chromium. Gemountet werden `LocalServer/Data`,
`LocalServer/logs` und `LocalServer/.env`, die Datenbank bleibt also beim Neubauen erhalten. Die
`.env` muss vor dem ersten `docker compose up` existieren, sonst legt Docker an ihrer Stelle einen
leeren Ordner an.

Kurzform zum Aktualisieren: `git pull && cd LocalServer/docker && docker compose up -d --build`

#### Variante B: lokal

```powershell
Set-Location .\LocalServer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

Alternativ `.\scripts\startServer.ps1` — das Skript nimmt das venv im Serverordner, falls vorhanden.

**Zusätzlich nötig: das Modul `ocr`.** Der Bandcamp-Provider löst Captchas mit einem eigenen
Rust-Modul, und `providers/Bandcamp/bandcamp_search.py` importiert es beim Laden. Fehlt es, startet
der Server gar nicht (`ModuleNotFoundError: No module named 'ocr'`).

Unter Windows liegt ein fertiges Wheel im Repository:

```powershell
pip install --force-reinstall ..\PythonModule\providers\ocr\ocr-0.1.0-cp39-abi3-win_amd64.whl
```

Auf anderen Systemen bauen und ins aktive venv installieren (Rust und maturin vorausgesetzt):

```bash
cd LocalServer/docker/captcha_ocr_source
pip install maturin
maturin develop --release
```

Das trainierte Modell liegt in `PythonModule/providers/ocr/` (`config.json`, `model.safetensors`).
Ausführliche Anleitung, auch für Linux ohne Docker: `LocalServer/docker/captcha_ocr_source/README.txt`.

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

#### Web-Frontend mit Docker

```powershell
Set-Location .\PyScrapperWebInterface
docker compose up -d --build      # danach http://localhost:8080
```

Das Image baut das Frontend und liefert es über nginx aus. nginx leitet `/api/...` (ohne das
Präfix) und `/stream/...` an den LocalServer weiter. Der Server ist nicht Teil dieser Compose-Datei,
sondern läuft separat (Docker oder lokal).

| Variable | Standard | Zweck |
|---|---|---|
| `BACKEND_URL` | `http://host.docker.internal:8000` | Adresse des LocalServers aus Sicht des Containers; passt zum Server-Container |
| `WEB_PORT` | `8080` | Port auf dem Host |

Läuft der Server lokal statt im Container, `BACKEND_URL=http://host.docker.internal:8765` setzen.
Der Container erreicht den Server dann über das Netzwerk des Hosts, nicht über dessen Loopback, also
muss der Server mit `--host 0.0.0.0` statt `127.0.0.1` gestartet werden. Damit ist er auch aus dem
lokalen Netz erreichbar.

---

## Voraussetzungen

| Was | Wofür |
|---|---|
| Python 3.11+ | Server und Engine (das Docker-Image nutzt 3.11) |
| .NET SDK 9.0 | Desktop-App |
| Node 20+ | Web-Frontend |
| ffmpeg / ffprobe | Codec-Prüfung und Konvertierung |
| Playwright Chromium | Provider, die auf Browser-Sniffing angewiesen sind |
| Rust + maturin | Bauen des Captcha-Moduls `ocr` (nur ohne Docker und nicht unter Windows) |
| Docker | Optional, für Server und Web-Frontend als Container |
| Windows | Nur für die Desktop-App: DPAPI, LibVLC-Cache und VC++-Redistributable sind Windows-spezifisch |

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
| `LocalServer/docker/` | Dockerfile und `compose.yaml` des Servers, Quellcode des `ocr`-Moduls |
| `PythonModule/providers/ocr/` | Trainiertes Captcha-Modell für den Bandcamp-Provider und fertiges Windows-Wheel |
| `PyScrapperWebInterface/docker-compose.yml` | Web-Frontend als Container |
| `HTML_Doku/` | Technische Dokumentation, Generator in `HTML_Doku/_generator/` |

---

## Gut zu wissen

- Der Server ist für den lokalen Betrieb gedacht und nicht für öffentliches Hosting ausgelegt.
- Die Desktop-App startet den Server nicht selbst — er muss vorher laufen.
- Das Web-Frontend ist experimentell. Es ruft den Server immer über `/api/...` auf; im
  Docker-Setup übersetzt nginx das. `npm run dev` hat dafür keinen Proxy in `vite.config.ts`.
- Die Desktop-App ist auf Port `8765` voreingestellt. Für den Server-Container auf `8000` den Port
  im Fenster *Config bearbeiten* ändern.
- Die Desktop-App leitet ihre Pfade aus dem Arbeitsverzeichnis ab und erwartet in der IDE den
  Ausführungspfad `bin/Debug/net9.0` innerhalb der Repository-Struktur.

---

## Schnellkommandos

```powershell
# Server-Health (lokal 8765, Docker 8000)
Invoke-RestMethod http://127.0.0.1:8765/health

# OpenAPI-Oberfläche
Start-Process http://127.0.0.1:8765/docs

# Logs mitlesen
Get-Content .\LocalServer\logs\server_runtime.log -Tail 100 -Wait
Get-Content .\PyScrapperDesktopApp\logs\app.log -Tail 100 -Wait

# Server-Container: Logs und Neustart
docker compose -f LocalServer/docker/compose.yaml logs -f
docker compose -f LocalServer/docker/compose.yaml restart
```
