# PyScrapper Desktop App - Frontend-Dokumentation

## 1. Architektur und Projektstruktur

Das Frontend der Desktop-Anwendung nutzt **C#** und das **Avalonia UI Framework**, um plattformübergreifend lauffähig zu sein. Es setzt konsequent auf das **MVVM-Muster (Model-View-ViewModel)**. Durch den Einsatz des `CommunityToolkit.Mvvm` (mit Source-Generatoren) wird Boilerplate-Code weitgehend vermieden.

Die Struktur des Projekts teilt sich in folgende Hauptbereiche auf:
* **Views** (`/Views`): Enthält die grafischen Oberflächen, geschrieben in XAML (`.axaml`) und einfachem Code-Behind. Hier finden sich Komponenten wie das `MainWindow`, `LauncherWindow` oder das `ScrapWindowWithSearch`.
* **ViewModels** (`/ViewModels`): Die Präsentations-Logik und das Data-Binding. Diese Klassen leiten von `ObservableObject` ab. Aktionen aus den Views werden hier über `[RelayCommand]` angesteuert, Properties via `[ObservableProperty]` an die View gebunden.
* **Models** (`/Models`): Reine Datenstrukturen, globale Zustände (`AppData.cs`) sowie Services wie der `ApiClient.cs` für das API-Handling oder `DatabaseOperations.cs` zur Interaktion mit der lokalen DB.

---

## 2. Ablauf und Funktionsweise (Control Flow)

Das Frontend agiert nie allein, sondern steht im Austausch mit zwei lokalen Systemen:
1. Eine lokale **SQLite Datenbank** für Einstellungen, Playlists und die Historie gecrawlter Medien.
2. Der im Hintergrund laufende **Python-Server**, welcher unter `http://127.0.0.1:8765` API-Routen wie `/search` und `/download` zur Verfügung stellt.

### Der Start-Lebenszyklus (Launcher & MainWindow)
Der gesamte Startprozess wird in der zentralen `App.axaml.cs` (`OnFrameworkInitializationCompleted`) gesteuert:

1. Zuerst lädt sich das `LauncherWindow`. Wenn der Start erfolgreich war, lädt Avalonia die App-Daten im Hintergrund.
2. `DatabaseOperations` liest Einstellungsdaten und alle bisherigen Downloads aus SQLite in das memory-basierte `AppData`.
3. Jeder Eintrag wird validiert: Existiert die Datei noch? Ist der Codec spielbar? Nicht lokalisierbare Medien werden auf "nicht spielbar" (`IsPlayable = false`) gesetzt oder entfernt.
4. Ein Scanner (`App.ScanFolder`) vergleicht den physischen Download-Ordner mit den App-Daten, um womöglich extern hinzugefügte Dateien nachträglich aufzunehmen.
5. Zum Schluss wird das `MainWindow` gestartet und öffnet dem Besucher die Ansicht (inkl. Theme Variant: Light/Dark Mode) seiner Bibliothek.

### Der Scraping-Ablauf (Sequence Workflow)

Wenn ein Suchvorgang samt Download (z.B. aus YouTube via `ScrapWindowWithSearchViewModel`) getriggert wird, läuft folgender Prozess ab:

> **Wichtiger Hinweis zum Diagramm:** 
> Da IDEs wie Rider Mermaid-Diagramme oft nicht direkt grafisch in Markdown rendern können, habe ich ein physisches und interaktives Flussdiagramm für dich erstellt. 
> 
> 👉 **Bitte öffne die Datei `Frontend_Flowchart.html` (im selben Ordner `Notes`) in deinem Webbrowser (Doppelklick)**. Dort siehst du ein korrekt gerendertes, sauberes Visualisierungs-Diagramm des kompletten Scraping-Ablaufs!

---

## 3. Code Style und Konventionen

Wenn man sich den Quellcode der ViewModels und Models (wie das `MainWindowViewModel.cs` oder `ApiClient.cs`) ansieht, erkennt man sehr klare Software-Engineering Richtlinien:

1. **MVVM via Annotationen**: 
   Dank `CommunityToolkit.Mvvm` werden private Felder wie `private string _searchQuery` dekoriert mit `[ObservableProperty]`. Zur Laufzeit wird dadurch automatisch die public Eigenschaft `SearchQuery` mitsamt `INotifyPropertyChanged`-Implementierung generiert. Selbiges gilt für asynchrone Tasks, die per `[RelayCommand]` direkt an Buttons gebunden werden.
2. **Asynchronität (Async / Await)**: 
   Sämtliche I/O Aktivitäten (File Picker, API Calls über den `HttpClient`, SQLite Abfragen) sind strikt asynchron aufgebaut. Das verhindert das Einfrieren (Freezing) der Avalonia GUI-Threads. 
3. **Zentrales Error-Handling und Logging**: 
   Aktionen sind konstant in `Try / Catch`-Blöcken verpackt. Fast alle auftretenden Fehler oder auch reguläre System-Ereignisse (wie der Scanner Diff) werden mit dem `AppLogger` (`new Massage(...)`) festgehalten. Die Logs landen in `app.log` und lassen sich auf Knopfdruck des Users über die Oberfläche anzeigen.
4. **Validierungs-Sicherheit**:
   Das Frontend vertraut Benutzereingaben nicht blind. Das ViewModel z.B. bei Dateinamen (`TryValidateFileName`) enthält interne Logik, welche System-Restriktionen von Windows-Betriebssystemen (wie die reservierten Namen `CON`, `PRN`, unzulässige Sonderzeichen oder Endungen mit Punkt/Leerzeichen) abfängt.
5. **Standardisierte Doku (XML-Comments)**:
   Ein sehr aufgeräumter Aspekt des Stils ist, dass wichtige Methoden und Klassen konsistent mit `/// <summary>` XML-Tags annotiert wurden. Das sorgt nicht nur dafür, dass Parameter und Returns (`<param>`, `<returns>`) in der IDE dokumentiert sind, sondern erleichtert auch stark das allgemeine Onboarding in der Codebase.


