# PyScrapper — Desktop-Dokumentation

Technische Dokumentation der PyScrapper-Desktopanwendung (C# / Avalonia / .NET 9).
Die HTML-Seiten sind im PyScrapper-Design gehalten und decken Architektur, Workflows und UI auf dem aktuellen Workspace-Stand ab.

## Startpunkt

- **`Index.html`** — Dokumentations-Portal mit Verweisen auf alle Seiten und einer Schnellreferenz.

## Hauptdokumente

### `Architecture_Professional.html`
Systemüberblick, MVVM-Schichten, Kern-Datenmodelle (`DownloadedMedia`, `Playlist`, `PlaylistMedia`,
`Settings`, `User`, `MediaFilter`), zentraler Zustand (`AppData`), Konfiguration & DPAPI-Sicherheit
(`AppConfig` / `SecretProtector`), API-Kommunikation (`ApiClient` / `Database`) und Technologie-Stack.

### `Workflows_Professional.html`
Startsequenz (Config → Login → Settings → Launcher → Datenladen → MainWindow), tatsächliches Launcher-Verhalten,
Such- und Download-Ablauf, Filterlogik und das gebündelte Speichern beim Beenden.

### `UI_Documentation.html`
Alle Fenster und Dialoge nach Rolle: Startsequenz (Login, Launcher), Hauptfenster, Scrap-Fenster,
Medien & Playlists sowie Werkzeuge und Dialoge (Filter, Codec-Konverter, Health, Config, Logs u.a.).

### `QuickStart.html`
Einstieg nach Aufgabe (neu / Feature / Bugfix), wichtige Code-Dateien und vier Schritte bis produktiv.

### `Developer_Guide.html`
Tiefer Einstieg zum Verstehen des Codes: Setup & Build, Projektstruktur, Konventionen (MVVM/Toolkit, Styling),
Service-Layer (Dialog/Storage/Logger), Interfaces, Logging im Detail, Audio-/Codec-Handling, Anleitung zum
Hinzufügen eines Features, Datenfluss an echten Beispielen, das Laufzeit-Verhalten der App und ein Glossar.

## Design

- Farbschema aus dem PyScrapper-Logo: Dunkelblau, Gold/Gelb, Blau — mit dezentem Sternenhintergrund.
- Konsistentes Layout, Navigation zurück zum Portal, responsives Raster.
- Diagramme mit Mermaid (Flow-, Sequenz-, Zustands- und Klassendiagramme).

## Schnellreferenz

### API-Endpoints
```
GET  /                        - Root-Status
POST /command                 - Server-Kommandos
POST /download                - Download starten
GET  /download/progress/{id}  - Fortschritt
POST /search                  - Suche
GET  /health                  - Serverstatus
POST /save                    - Gebündeltes Speichern
POST /login                   - Anmeldung
POST /register                - Registrierung
POST /logout/{identifier}     - Logout
```

### Kernklassen
```
DownloadedMedia   - Ein gespeicherter Medien-Eintrag
Playlist          - Sammlung von Medien
PlaylistMedia     - Zuordnung Medium <-> Playlist (+ Position)
Settings          - Nutzer-Einstellungen
MediaFilter       - Filterkriterien
AppConfig         - App-Konfiguration (verschlüsselter API-Key)
ApiClient         - HTTP-Kommunikation mit dem Backend
Database          - CRUD gegen die API
```

---

**Dokumentationsstand:** 4. August 2026
**Format:** HTML5 + CSS + Mermaid
