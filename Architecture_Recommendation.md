# Architektur-Empfehlung: Wichtige Interfaces für PyScrapper

Um die Testbarkeit zu erhöhen und die Kopplung zwischen Logik und UI zu verringern, sollten folgende Interfaces in die App implementiert werden.

---

## 1. IAppDataService
**Zweck:** Ablösung der statischen `AppData`-Klasse. Ermöglicht isolierte Testumgebungen ohne Daten-Vermischung zwischen Tests.

### Implementierung:
```csharp
public interface IAppDataService
{
    ObservableCollection<DownloadedMedia> DownloadedMedias { get; }
    ObservableCollection<Playlist> Playlists { get; }
    Settings Settings { get; }
    
    void AddDownloadedMedia(DownloadedMedia media);
    void RemoveDownloadedMedia(DownloadedMedia media);
    bool MediaAlreadyExists(string filePath);
}

// In der App (Einmalige Instanz/Singleton)
public class AppDataService : IAppDataService 
{
    public ObservableCollection<DownloadedMedia> DownloadedMedias { get; } = new();
    // ... Implementierung der Methoden ...
}
```

---

## 2. IDialogService
**Zweck:** Ersetzt direkte Aufrufe von `MessageBox.ShowDialog()` und `Window.Close()`. Dies löst das aktuelle Problem mit der `InvalidOperationException` in den Tests.

### Implementierung:
```csharp
public interface IDialogService
{
    Task ShowAlertAsync(string message);
    Task<bool> ConfirmAsync(string message);
    Task<string?> AskInputAsync(string prompt);
}

// Implementierung nutzt Avalonia-Fenster
public class AvaloniaDialogService(Window owner) : IDialogService
{
    public async Task ShowAlertAsync(string message) 
        => await new MessageBox(message).ShowDialog(owner);
        
    public async Task<bool> ConfirmAsync(string message)
        => await new ConfirmationWindow(message).ShowDialog<bool>(owner);
}
```

---

## 3. IAudioPlayerService
**Zweck:** Abstraktion der VLC-Wiedergabe. Im Test kann so der "echte" Player durch einen Dummy ersetzt werden, damit Tests nicht versuchen, Audio-Hardware anzusprechen.

### Implementierung:
```csharp
public interface IAudioPlayerService
{
    bool IsPlaying { get; }
    void Play(string filePath);
    void Stop();
    void SetVolume(int volume);
    event Action<string> TrackChanged;
}
```

---

## 4. IFileService / IStorageService
**Zweck:** Kapselung von Dateisystem-Operationen (`File.Exists`, `Directory.CreateDirectory`). Verhindert, dass Tests "echte" Dateien auf der Festplatte erstellen oder löschen müssen.

### Implementierung:
```csharp
public interface IFileService
{
    bool Exists(string path);
    void SaveAllText(string path, string content);
    string ReadAllText(string path);
    void Delete(string path);
}
```

---

## Umsetzung: Dependency Injection (DI)

### Im ViewModel:
Statt auf statische Klassen zuzugreifen, werden die Interfaces über den Konstruktor "reingereicht":

```csharp
public class MainViewModel : ObservableObject
{
    private readonly IAppDataService _dataService;
    private readonly IDialogService _dialogService;

    public MainViewModel(IAppDataService dataService, IDialogService dialogService)
    {
        _dataService = dataService;
        _dialogService = dialogService;
    }

    public async Task AddMedia()
    {
        if (_dataService.MediaAlreadyExists("..."))
        {
            await _dialogService.ShowAlertAsync("Existiert bereits!");
        }
    }
}
```

### Im Test (Beispiel mit Moq):
```csharp
[Fact]
public async Task Test_AddMedia_ShowsAlert_IfDuplicate()
{
    // Setup
    var mockData = new Mock<IAppDataService>();
    mockData.Setup(d => d.MediaAlreadyExists(It.IsAny<string>())).Returns(true);
    var mockDialog = new Mock<IDialogService>();
    
    var vm = new MainViewModel(mockData.Object, mockDialog.Object);

    // Act
    await vm.AddMedia();

    // Assert: Wurde der Alarm ausgelöst?
    mockDialog.Verify(d => d.ShowAlertAsync("Existiert bereits!"), Times.Once);
}
```

Durch diese Struktur können wir jeden Teil der App testen, ohne ein einziges Fenster öffnen oder eine Datei schreiben zu müssen.

