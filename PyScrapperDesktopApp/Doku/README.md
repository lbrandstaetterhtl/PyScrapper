# PyScrapper Dokumentation - Überblick

## Überblick

Dieser Ordner enthält die vollständige technische Dokumentation der PyScrapper-Anwendung. 
Die Dokumentation ist in mehrere HTML-Dateien aufgeteilt, um leichte Lesbarkeit und professionelle Präsentation zu gewährleisten.

## Datei-Struktur

### 🎯 Startpunkt
- **Index.html** - Haupt-Dokumentations-Portal mit Links zu allen anderen Dokumenten

### 📚 Hauptdokumentation (Professionell)

#### 1. Architecture_Professional.html
**Inhalte:**
- Kern-Datenmodelle (DownloadedMedia, Playlist, Settings, MediaFilter)
- System-Architektur Übersicht (MVVM Pattern)
- Request/Response Modelle für API-Kommunikation
- SQLite Datenbankstruktur
- Alle ViewModels und deren Aufgaben
- Technologie-Stack
- Beispiel: Datenfluss beim Download

**Zielgruppe:** Entwickler, Architekten

---

#### 2. Workflows_Professional.html
**Inhalte:**
- Download Workflow (Suche → Download → Fortschritt)
- Anwendungs-Initialisierung (Boot Sequence)
- Filter-Anwendung Logik
- Musik-Player State Machine
- MVVM Data Binding Mechanism

**Zielgruppe:** Entwickler, Projektmanager

---

#### 3. UI_Documentation.html
**Inhalte:**
- Hauptfenster (MainWindow) - Layout & Funktionen
- Suche & Download Dialog (ScrapWindow)
- Filter Dialog (FilterWindow)
- Playlist Erstellen Dialog
- Video Konverter Window (FFmpeg)
- Download-Fortschritt Window
- Server Health Monitor Window

**Zielgruppe:** UI/UX Entwickler, Produktmanager

---

### 📖 Zusätzliche Dokumentation (Vereinfacht)

#### 4. Frontend_Flowchart_Improved.html
- Verbesserte Versionen der Workflows mit besserer Struktur
- Farb-Legende für verschiedene Prozesstypen

#### 5. UI_Windows_Guide.html
- Benutzerfreundliche Ansicht aller Fenster
- Mit Mock-ups und Beschreibungen

#### 6. DataModels_Simplified.html
- Vereinfachte Erklärung der Datenmodelle
- Mit Beispielen und visuellen Diagrammen

---

### 📋 Original Dokumentation (Legacy)

Diese Dateien sind noch vorhanden für Rückwärts-Kompatibilität:
- **AllDataModels.html** - Original Klassendiagramme
- **Frontend_Flowchart_Detailed.html** - Detaillierte Workflows (alte Version)
- **WindowTreesWithMockups.html** - Fenster mit Mock-ups (alte Version)
- **Frontend_Doku.md** - Markdown Dokumentation

---

## Wie man die Dokumentation nutzt

### 1. Für neue Entwickler
```
Starten Sie mit: Index.html
↓
Architecture_Professional.html (Verstehen Sie die Struktur)
↓
Workflows_Professional.html (Verstehen Sie die Prozesse)
↓
UI_Documentation.html (Kennen Sie die Fenster)
```

### 2. Für Feature-Entwicklung
```
1. Architecture_Professional.html (Wo speichern die Daten?)
2. Workflows_Professional.html (Welcher Prozess ist relevant?)
3. UI_Documentation.html (Welche Fenster sind involviert?)
```

### 3. Für Bug-Fixes
```
1. Workflows_Professional.html (Wo kann das Problem sein?)
2. Architecture_Professional.html (Datenfluss prüfen)
3. UI_Documentation.html (UI-spezifisches Problem?)
```

---

## Technologien in den Diagrammen

### Mermaid Diagramme
- **Flowcharts:** Prozessabläufe visualisieren
- **Class Diagrams:** Datenmodelle und Beziehungen
- **Graph TD:** Hierarchische Strukturen

### Features
- **Pan & Zoom:** Mit Maus scrollen und zoomen möglich
- **Responsive:** Funktioniert auf allen Bildschirmgrößen
- **Dark Theme:** Professionelle dunkle Farbgebung

---

## Design-Prinzipien

✓ **Professionell:** Business-gerechte Ästhetik
✓ **Klar:** Strukturiert und leicht zu folgen
✓ **Komplett:** Alle Aspekte abgedeckt
✓ **Wartbar:** Einfach zu aktualisieren
✓ **Zugänglich:** Für alle Erfahrungsstufen geeignet

---

## Schnelle Referenz

### API-Endpoints
```
POST /search           - Video suchen
POST /download         - Download starten
GET /download/progress/{id} - Fortschritt abrufen
GET /health           - Server-Status prüfen
```

### Wichtige Klassen
```
DownloadedMedia       - Ein heruntergeladenes Video
Playlist              - Sammlung von Videos
Settings              - App-Konfiguration
MediaFilter           - Filter für Video-Suche
ApiClient             - HTTP Kommunikation
```

### ViewModels
```
MainWindowViewModel           - Hauptfenster Logik
ScrapWindowViewModel          - Suche & Download
MediaPlayerControlViewModel   - Musik-Abspieler
FilterWindowViewModel         - Filter-Dialog
ProgressBarWindowViewModel    - Download-Fortschritt
```

---

## Kontakt & Support

Bei Fragen zur Dokumentation oder Problemen mit den Diagrammen:
- Prüfen Sie zuerst Index.html
- Konsultieren Sie Architecture_Professional.html
- Wenden Sie sich an das Entwicklungsteam

---

**Dokumentation Version:** 1.0
**Aktualisiert:** 27. Mai 2026
**Format:** HTML5 + Mermaid Diagramme + CSS

