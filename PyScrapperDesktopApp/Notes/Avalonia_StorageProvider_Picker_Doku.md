# Avalonia StorageProvider – File & Folder Picker Dokumentation

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Zugriff auf den StorageProvider](#zugriff-auf-den-storageprovider)
3. [OpenFilePickerAsync – Datei(en) öffnen](#openfilepickerasync)
4. [SaveFilePickerAsync – Datei speichern](#savefilepickerasync)
5. [OpenFolderPickerAsync – Ordner auswählen](#openfolderpickerasync)
6. [FilePickerFileType – Dateifilter](#filepickerfiletype)
7. [IStorageFile & IStorageFolder – Ergebnistypen](#istoragefile--istoragefolder)
8. [MVVM-Integration (empfohlen)](#mvvm-integration)
9. [Häufige Fehler & Fallstricke](#häufige-fehler--fallstricke)

---

## Übersicht

Avalonia stellt Datei- und Ordnerauswahl-Dialoge über `TopLevel.StorageProvider` bereit.
Diese sind **immer async** und geben plattformspezifische native Dialoge zurück (Windows Explorer, GTK, macOS Finder etc.).

| Methode                    | Zweck                       | Rückgabe                        |
|----------------------------|-----------------------------|---------------------------------|
| `OpenFilePickerAsync`      | Eine oder mehrere Dateien öffnen | `IReadOnlyList<IStorageFile>`  |
| `SaveFilePickerAsync`      | Speicherpfad für Datei wählen   | `IStorageFile?`                |
| `OpenFolderPickerAsync`    | Einen oder mehrere Ordner wählen | `IReadOnlyList<IStorageFolder>` |

---

## Zugriff auf den StorageProvider

`StorageProvider` gehört zu `TopLevel` — dem Root-Element jedes Avalonia-Fensters.

### Im Code-behind (einfachster Weg)

```csharp
var topLevel = TopLevel.GetTopLevel(this); // "this" = das Window oder Control
var storageProvider = topLevel!.StorageProvider;
```

### Aus einem UserControl heraus

```csharp
var topLevel = TopLevel.GetTopLevel(myControl);
```

### Aus dem ViewModel (MVVM-konform)

Direkte Referenz auf `TopLevel` im ViewModel ist schlecht (koppelt ViewModel ans View).
→ Stattdessen ein Interface verwenden. Siehe [MVVM-Integration](#mvvm-integration).

---

## OpenFilePickerAsync

Öffnet einen Dialog zur Dateiauswahl.

### Signatur

```csharp
Task<IReadOnlyList<IStorageFile>> OpenFilePickerAsync(FilePickerOpenOptions options)
```

### FilePickerOpenOptions

| Property          | Typ                              | Beschreibung                                      |
|-------------------|----------------------------------|---------------------------------------------------|
| `Title`           | `string?`                        | Fenstertitel des Dialogs                          |
| `AllowMultiple`   | `bool`                           | Mehrfachauswahl erlauben (default: `false`)       |
| `FileTypeFilter`  | `IReadOnlyList<FilePickerFileType>?` | Erlaubte Dateitypen (Filter-Dropdown)         |
| `SuggestedStartLocation` | `IStorageFolder?`         | Startverzeichnis beim Öffnen des Dialogs          |

### Beispiel – Einzelne Datei

```csharp
var files = await storageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
{
    Title = "Datei öffnen",
    AllowMultiple = false,
    FileTypeFilter = new[]
    {
        new FilePickerFileType("MP3-Dateien") { Patterns = new[] { "*.mp3" } },
        FilePickerFileTypes.All
    }
});

if (files.Count > 0)
{
    string path = files[0].Path.LocalPath;
    // path = "C:\Users\Leon\Music\song.mp3"
}
```

### Beispiel – Mehrere Dateien

```csharp
var files = await storageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
{
    Title = "Dateien auswählen",
    AllowMultiple = true,
    FileTypeFilter = new[]
    {
        new FilePickerFileType("Mediendateien")
        {
            Patterns = new[] { "*.mp3", "*.mp4", "*.mkv", "*.wav", "*.flac" }
        }
    }
});

foreach (var file in files)
{
    Console.WriteLine(file.Path.LocalPath);
}
```

---

## SaveFilePickerAsync

Öffnet einen "Speichern unter"-Dialog.

### Signatur

```csharp
Task<IStorageFile?> SaveFilePickerAsync(FilePickerSaveOptions options)
```

### FilePickerSaveOptions

| Property                  | Typ                              | Beschreibung                                      |
|---------------------------|----------------------------------|---------------------------------------------------|
| `Title`                   | `string?`                        | Fenstertitel des Dialogs                          |
| `SuggestedFileName`       | `string?`                        | Vorausgefüllter Dateiname                         |
| `DefaultExtension`        | `string?`                        | Standarderweiterung wenn keine angegeben (z.B. `"json"`) |
| `FileTypeChoices`         | `IReadOnlyList<FilePickerFileType>?` | Erlaubte Dateitypen                           |
| `SuggestedStartLocation`  | `IStorageFolder?`                | Startverzeichnis                                  |

### Beispiel

```csharp
var file = await storageProvider.SaveFilePickerAsync(new FilePickerSaveOptions
{
    Title = "Playlist speichern",
    SuggestedFileName = "meine_playlist",
    DefaultExtension = "json",
    FileTypeChoices = new[]
    {
        new FilePickerFileType("JSON") { Patterns = new[] { "*.json" } }
    }
});

if (file != null)
{
    string path = file.Path.LocalPath;
    await File.WriteAllTextAsync(path, jsonContent);
}
```

---

## OpenFolderPickerAsync

Öffnet einen Dialog zur Ordnerauswahl.

### Signatur

```csharp
Task<IReadOnlyList<IStorageFolder>> OpenFolderPickerAsync(FolderPickerOpenOptions options)
```

### FolderPickerOpenOptions

| Property                  | Typ               | Beschreibung                                      |
|---------------------------|-------------------|---------------------------------------------------|
| `Title`                   | `string?`         | Fenstertitel des Dialogs                          |
| `AllowMultiple`           | `bool`            | Mehrere Ordner auswählen (default: `false`)       |
| `SuggestedStartLocation`  | `IStorageFolder?` | Startverzeichnis                                  |

### Beispiel

```csharp
var folders = await storageProvider.OpenFolderPickerAsync(new FolderPickerOpenOptions
{
    Title = "Musikordner auswählen",
    AllowMultiple = false
});

if (folders.Count > 0)
{
    string folderPath = folders[0].Path.LocalPath;
    // folderPath = "D:\Music"
}
```

---

## FilePickerFileType – Dateifilter

Mit `FilePickerFileType` definierst du, welche Dateien im Dialog angezeigt werden.

### Aufbau

```csharp
new FilePickerFileType("Anzeigename")
{
    Patterns = new[] { "*.mp3", "*.flac" },   // Glob-Pattern (Windows/Linux)
    MimeTypes = new[] { "audio/mpeg" },        // MIME-Typ (Linux/macOS bevorzugt)
    AppleUniformTypeIdentifiers = new[] { "public.mp3" } // macOS UTI
}
```

> **Hinweis:** Auf Linux wird `MimeTypes` bevorzugt, auf Windows `Patterns`, auf macOS `AppleUniformTypeIdentifiers`.
> Für maximale Kompatibilität immer alle drei setzen.

### Vordefinierte Typen (Avalonia built-in)

```csharp
FilePickerFileTypes.All          // Alle Dateien (*.*)
FilePickerFileTypes.ImageAll     // Alle Bildformate
FilePickerFileTypes.ImageJpg     // JPEG
FilePickerFileTypes.ImagePng     // PNG
FilePickerFileTypes.TextPlain    // Textdateien
FilePickerFileTypes.Pdf          // PDF
```

### Eigene Typen als statische Felder (Empfehlung)

```csharp
public static class AppFileTypes
{
    public static FilePickerFileType Audio { get; } = new("Audiodateien")
    {
        Patterns = new[] { "*.mp3", "*.flac", "*.wav", "*.ogg", "*.m4a" },
        MimeTypes = new[] { "audio/*" }
    };

    public static FilePickerFileType Video { get; } = new("Videodateien")
    {
        Patterns = new[] { "*.mp4", "*.mkv", "*.avi", "*.mov" },
        MimeTypes = new[] { "video/*" }
    };

    public static FilePickerFileType Media { get; } = new("Alle Mediendateien")
    {
        Patterns = new[] { "*.mp3", "*.mp4", "*.flac", "*.wav", "*.mkv", "*.avi" },
        MimeTypes = new[] { "audio/*", "video/*" }
    };
}
```

Verwendung:

```csharp
FileTypeFilter = new[] { AppFileTypes.Media, AppFileTypes.Audio, FilePickerFileTypes.All }
```

---

## IStorageFile & IStorageFolder – Ergebnistypen

### IStorageFile

```csharp
IStorageFile file = files[0];

string localPath = file.Path.LocalPath;   // Absoluter Pfad als string
Uri uri          = file.Path;             // Als Uri
string name      = file.Name;            // Nur Dateiname mit Extension

// Datei lesen über Stream
await using var stream = await file.OpenReadAsync();
using var reader = new StreamReader(stream);
string content = await reader.ReadToEndAsync();

// Datei schreiben (nur bei SaveFilePicker-Ergebnis sinnvoll)
await using var writeStream = await file.OpenWriteAsync();
```

### IStorageFolder

```csharp
IStorageFolder folder = folders[0];

string localPath = folder.Path.LocalPath; // Absoluter Pfad als string
string name      = folder.Name;           // Nur Ordnername

// Inhalt des Ordners auflisten
await foreach (var item in folder.GetItemsAsync())
{
    if (item is IStorageFile f)
        Console.WriteLine($"Datei: {f.Name}");
    else if (item is IStorageFolder sub)
        Console.WriteLine($"Unterordner: {sub.Name}");
}
```

### SuggestedStartLocation – Startverzeichnis setzen

```csharp
// Aus absolutem Pfad einen IStorageFolder erstellen
IStorageFolder? startFolder = await storageProvider.TryGetFolderFromPathAsync(
    new Uri("file:///D:/Music")
);

var folders = await storageProvider.OpenFolderPickerAsync(new FolderPickerOpenOptions
{
    SuggestedStartLocation = startFolder
});
```

---

## MVVM-Integration

Im MVVM-Pattern darf das ViewModel kein direktes `TopLevel`/`Window` referenzieren.
Die saubere Lösung: ein Interface, das im View implementiert und per DI/Constructor ins ViewModel gegeben wird.

### Schritt 1 – Interface definieren

```csharp
// Services/IStorageService.cs
public interface IStorageService
{
    Task<IReadOnlyList<IStorageFile>> OpenFilePickerAsync(FilePickerOpenOptions options);
    Task<IStorageFile?> SaveFilePickerAsync(FilePickerSaveOptions options);
    Task<IReadOnlyList<IStorageFolder>> OpenFolderPickerAsync(FolderPickerOpenOptions options);
}
```

### Schritt 2 – Implementierung im View-Layer

```csharp
// Services/StorageService.cs
public class StorageService : IStorageService
{
    private readonly TopLevel _topLevel;

    public StorageService(TopLevel topLevel)
    {
        _topLevel = topLevel;
    }

    public Task<IReadOnlyList<IStorageFile>> OpenFilePickerAsync(FilePickerOpenOptions options)
        => _topLevel.StorageProvider.OpenFilePickerAsync(options);

    public Task<IStorageFile?> SaveFilePickerAsync(FilePickerSaveOptions options)
        => _topLevel.StorageProvider.SaveFilePickerAsync(options);

    public Task<IReadOnlyList<IStorageFolder>> OpenFolderPickerAsync(FolderPickerOpenOptions options)
        => _topLevel.StorageProvider.OpenFolderPickerAsync(options);
}
```

### Schritt 3 – Im Window registrieren

```csharp
// MainWindow.axaml.cs
public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();

        var storageService = new StorageService(TopLevel.GetTopLevel(this)!);
        DataContext = new MainViewModel(storageService);
    }
}
```

### Schritt 4 – Im ViewModel verwenden

```csharp
// ViewModels/MainViewModel.cs
public partial class MainViewModel : ObservableObject
{
    private readonly IStorageService _storageService;

    [ObservableProperty]
    private string _selectedFolderPath = "";

    [ObservableProperty]
    private ObservableCollection<string> _selectedFiles = new();

    public MainViewModel(IStorageService storageService)
    {
        _storageService = storageService;
    }

    [RelayCommand]
    private async Task PickFolder()
    {
        var folders = await _storageService.OpenFolderPickerAsync(new FolderPickerOpenOptions
        {
            Title = "Ordner auswählen",
            AllowMultiple = false
        });

        if (folders.Count > 0)
            SelectedFolderPath = folders[0].Path.LocalPath;
    }

    [RelayCommand]
    private async Task PickFiles()
    {
        var files = await _storageService.OpenFilePickerAsync(new FilePickerOpenOptions
        {
            Title = "Dateien auswählen",
            AllowMultiple = true,
            FileTypeFilter = new[] { AppFileTypes.Media, FilePickerFileTypes.All }
        });

        SelectedFiles.Clear();
        foreach (var file in files)
            SelectedFiles.Add(file.Path.LocalPath);
    }
}
```

### XAML-Anbindung

```xml
<StackPanel Spacing="8">
    <Button Content="Ordner auswählen" Command="{Binding PickFolderCommand}" />
    <TextBlock Text="{Binding SelectedFolderPath}" />

    <Button Content="Dateien auswählen" Command="{Binding PickFilesCommand}" />
    <ItemsControl ItemsSource="{Binding SelectedFiles}">
        <ItemsControl.ItemTemplate>
            <DataTemplate>
                <TextBlock Text="{Binding}" />
            </DataTemplate>
        </ItemsControl.ItemTemplate>
    </ItemsControl>
</StackPanel>
```

---

## Häufige Fehler & Fallstricke

### `TopLevel.GetTopLevel(this)` gibt `null` zurück

**Ursache:** Das Control ist noch nicht im Visual Tree (z.B. Aufruf im Konstruktor vor `InitializeComponent`).

**Fix:** Sicherstellen, dass der Aufruf nach dem Laden des Fensters passiert (z.B. im `Loaded`-Event oder beim Button-Click).

```csharp
// ❌ Falsch – zu früh
public MainWindow()
{
    var tl = TopLevel.GetTopLevel(this); // null!
    InitializeComponent();
}

// ✅ Richtig – nach InitializeComponent
public MainWindow()
{
    InitializeComponent();
    var tl = TopLevel.GetTopLevel(this); // korrekt
}
```

---

### `files.Count == 0` nach Abbrechen

Das ist normales Verhalten – der User hat abgebrochen. **Immer auf leere Liste prüfen**, nie blindlings auf Index 0 zugreifen.

```csharp
// ❌ Falsch
string path = files[0].Path.LocalPath; // IndexOutOfRangeException wenn abgebrochen

// ✅ Richtig
if (files.Count > 0)
    string path = files[0].Path.LocalPath;
```

---

### `SaveFilePickerAsync` gibt `null` zurück

Selbe Ursache wie oben – User hat abgebrochen. Rückgabe ist `IStorageFile?`, also nullable.

```csharp
var file = await storageProvider.SaveFilePickerAsync(options);
if (file is null) return; // abgebrochen
```

---

### `Path.LocalPath` vs `Path.AbsoluteUri`

```csharp
file.Path.LocalPath     // "C:\Users\Leon\song.mp3" oder "/home/leon/song.mp3"
file.Path.AbsoluteUri   // "file:///C:/Users/Leon/song.mp3"
```

Für Dateioperationen mit `System.IO` immer `LocalPath` verwenden.

---

### Picker funktioniert nicht in Headless-Tests

`StorageProvider` benötigt ein echtes Fenster. In Unit-Tests ein Mock von `IStorageService` verwenden – das ist ein weiterer Grund, warum das Interface-Pattern aus dem [MVVM-Abschnitt](#mvvm-integration) empfohlen wird.
