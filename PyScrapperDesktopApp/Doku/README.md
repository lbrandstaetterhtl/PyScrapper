# PyScrapper Dokumentation - Überblick

## Überblick

Dieser Ordner enthält die aktuelle technische Dokumentation der PyScrapper-Desktopanwendung.
Die HTML-Seiten sind aufeinander abgestimmt und decken Architektur, Workflows und UI-Fenster ab.

## Datei-Struktur

### Startpunkt
- **`Index.html`** – zentrales Dokumentations-Portal mit Verweisen auf alle Hauptdokumente

### Hauptdokumentation

#### 1. `Architecture_Professional.html`
**Inhalte:**
- Kern-Datenmodelle: `DownloadedMedia`, `Playlist`, `Settings`, `MediaFilter`
- MVVM-Architektur und Zuständigkeiten der Schichten
- Request-/Response-Modelle für die API-Kommunikation
- SQLite-Datenbankstruktur und Persistenz
- Wichtige ViewModels und ihre Aufgaben
- Technologie-Stack der Desktop-App

**Zielgruppe:** Entwickler, Architekten

#### 2. `Workflows_Professional.html`
**Inhalte:**
- Such- und Download-Workflow
- Initialisierung der Anwendung
- Filter-Anwendung und Rücksetzen
- Audio-/Video-Wiedergabe als Zustandsmodell
- MVVM-Data-Binding und UI-Aktualisierung

**Zielgruppe:** Entwickler, Projektmanager

#### 3. `UI_Documentation.html`
**Inhalte:**
- Hauptfenster (`MainWindow`)
- Such- und Download-Fenster (`ScrapWindowWithSearch`)
- Filter-Dialog (`FilterWindow`)
- Playlist-Erstellung, Codec-Konvertierung, Fortschritt und Health-Check
- Zusätzliche Fenster wie `LauncherWindow`, `InputWindow`, `MessageBox`

**Zielgruppe:** UI/UX-Entwickler, Produktmanager

## Wie man die Dokumentation nutzt

### Für neue Entwickler
1. `Index.html`
2. `Architecture_Professional.html`
3. `Workflows_Professional.html`
4. `UI_Documentation.html`

### Für Feature-Entwicklung
1. Architektur prüfen: Daten, Modelle, API
2. Workflows prüfen: betroffene Prozesse und Zustände
3. UI prüfen: betroffene Fenster und Dialoge

### Für Bug-Fixes
1. `Workflows_Professional.html` – Prozesskette eingrenzen
2. `Architecture_Professional.html` – Datenfluss und Persistenz prüfen
3. `UI_Documentation.html` – betroffene Oberfläche identifizieren

## Technologien in den Diagrammen

### Mermaid-Diagramme
- Flowcharts für Prozessabläufe
- Class-Diagramme für Datenmodelle
- Graph-Darstellungen für Systemstrukturen

### Darstellung
- Pan & Zoom für größere Diagramme
- Responsives Layout für verschiedene Bildschirmgrößen
- Dunkles, konsistentes Doku-Design

## Design-Prinzipien

✓ Professionell und ruhig lesbar
✓ Klar strukturiert und schnell navigierbar
✓ Inhaltlich an der aktuellen Codebasis orientiert
✓ Wartbar und leicht erweiterbar

## Schnelle Referenz

### API-Endpoints
```
POST /search                  - Suche an den Server senden
POST /download                - Download starten
GET  /download/progress/{id}  - Download-Fortschritt abrufen
GET  /health                  - Serverstatus prüfen
```

### Wichtige Klassen
```
DownloadedMedia   - Ein gespeicherter Medien-Eintrag
Playlist          - Sammlung von Medien-IDs
Settings          - App-Konfiguration
MediaFilter       - Filterkriterien für die Medienliste
ApiClient         - HTTP-Kommunikation mit dem Backend
```

### Wichtige ViewModels
```
MainWindowViewModel            - Hauptfenster-Logik
ScrapWindowWithSearchViewModel - Suche & Download mit Provider-Auswahl
SunoScrapWindowViewModel       - Direkt-Download über URL
FilterWindowViewModel          - Filter-Dialog
ProgressBarWindowViewModel     - Fortschrittsanzeige
GetServerHealthWindowViewModel - Server-Health-Ansicht
MediaPlayerControlViewModel    - Medienwiedergabe
```

## Kontakt & Support

Bei Fragen zur Doku:
- zuerst `Index.html` öffnen
- dann `Architecture_Professional.html` lesen
- anschließend bei Bedarf `Workflows_Professional.html` und `UI_Documentation.html` prüfen

---

**Dokumentationsstand:** aktualisiert am 5. Juni 2026
**Format:** HTML5 + CSS + Mermaid

