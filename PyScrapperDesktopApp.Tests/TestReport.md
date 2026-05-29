# Testbericht - Unit Tests (Desktop App)

**Datum:** 29. Mai 2026
**Umgebung:** Windows PowerShell, .NET 9.0
**Zusammenfassung:**
*   **Insgesamt:** 105 Tests
*   **Erfolgreich:** 104 Tests
*   **Fehlgeschlagen:** 1 Test

---

## Fehlgeschlagene Tests

### 1. `PyScrapperDesktopApp.Tests.ViewModels.CreatePlaylistWindowViewModelTests.CreatePlaylist_WithEmptyName_DoesNotAddPlaylist`

*   **Fehlertyp:** `System.InvalidOperationException`
*   **Meldung:** `Cannot show window with non-visible owner.`
*   **Ort:** `CreatePlaylistWindowViewModel.cs`, Zeile 58 (in der Methode `CreatePlaylist`)
*   **Ursache:**
    Innerhalb der Methode `CreatePlaylist` im ViewModel wird im Falle eines leeren Playlist-Namens eine `MessageBox` (ein `Window`) instanziiert und mittels `ShowDialog(_createPlaylistWindow)` angezeigt.
    Im Testumfeld (Unit Test) wird das ViewModel mit einem neu erstellten `Window`-Objekt initialisiert (`new Window()`), welches jedoch nie mit `.Show()` sichtbar gemacht wurde.
    Avalonia verbietet es, einen Dialog (`ShowDialog`) für ein "Owner"-Fenster anzuzeigen, das selbst nicht sichtbar ist. Dies führt zum Abbruch des Tests mit der beschriebenen Exception, noch bevor die Validierung (`Assert.Empty(AppData.Playlists)`) erreicht wird.

---

## Analyse & Empfehlung (Fixing deaktiviert gemäß Anweisung)

Das Problem resultiert aus einer harten Abhängigkeit der ViewModels von UI-Elementen (`Window`, `MessageBox`) für Benutzerrückmeldungen. 
*   **Warum es fehlschlägt:** Der Test will nur die logische Prüfung (Name leer -> kein Playlist-Eintrag) testen, wird aber von der UI-Interaktion (`ShowDialog`) blockiert.
*   **Theoretischer Lösungsansatz:** Einführung eines Abstraktions-Layers (z. B. ein `IDialogService`), der im Test gemockt werden kann, oder das Sicherstellen der Sichtbarkeit des Fensters innerhalb der `AvaloniaFixture` (was jedoch bei Headless-Tests komplex sein kann).

---

## Lösungsvorschlag (Best Practice)

Um diesen Fehler zu beheben und die Testbarkeit zu verbessern, sollte die direkte Abhängigkeit zur UI (`MessageBox`, `Window.ShowDialog`) durch eine Abstraktion ersetzt werden.

### 1. Definition eines Dialog-Service
Zuerst wird ein Interface in `PyScrapperDesktopApp.Models.Interfaces` (oder einem ähnlichen Namespace) erstellt:

```csharp
public interface IDialogService
{
    Task ShowMessageAsync(string message);
    // Weitere Methoden wie AskConfirmationAsync etc.
}
```

### 2. Implementierung in der App
In der App wird dieses Interface implementiert:

```csharp
public class AvaloniaDialogService : IDialogService
{
    private readonly Window _owner;
    public AvaloniaDialogService(Window owner) => _owner = owner;

    public async Task ShowMessageAsync(string message)
    {
        var mb = new MessageBox(message);
        await mb.ShowDialog(_owner);
    }
}
```

### 3. Anpassung des ViewModels
Das ViewModel nutzt nun den Service statt die Klasse `MessageBox` direkt zu instanziieren:

```csharp
public partial class CreatePlaylistWindowViewModel : ObservableObject
{
    private readonly IDialogService _dialogService;
    // ...

    public CreatePlaylistWindowViewModel(Window window, IDialogService dialogService)
    {
        _dialogService = dialogService;
        // ...
    }

    [RelayCommand]
    private async Task CreatePlaylist()
    {
        if (string.IsNullOrWhiteSpace(PlaylistName))
        {
            await _dialogService.ShowMessageAsync("Playlist name cannot be empty.");
            return;
        }
        // ... Logik zum Erstellen ...
    }
}
```

### 4. Lösung im Unit Test
Im Test kann nun ein "Mock" (ein Platzhalter) verwendet werden, der nichts tut, wodurch die `InvalidOperationException` vermieden wird:

```csharp
// Im Test mit Moq:
var mockDialogService = new Mock<IDialogService>();
var vm = new CreatePlaylistWindowViewModel(new Window(), mockDialogService.Object);

// Der Aufruf von CreatePlaylist wird nun nicht mehr versuchen, ein Fenster zu öffnen.
vm.CreatePlaylistCommand.Execute(null); 

// Verifizierung, dass die Nachricht "gezeigt" wurde:
mockDialogService.Verify(s => s.ShowMessageAsync("Playlist name cannot be empty."), Times.Once);
```

### Warum löst ein Interface dieses Problem?

Ein Interface fungiert als **Vertrag**. Es definiert, *was* getan werden kann (z. B. eine Nachricht anzeigen), ohne festzulegen, *wie* es technisch umgesetzt wird.

#### 1. Entkopplung (Decoupling)
Ohne Interface ist das ViewModel "fest verdrahtet" mit der Klasse `MessageBox`. Da `MessageBox` ein echtes Fenster ist, benötigt es eine laufende grafische Oberfläche. Ein Interface bricht diese harte Verbindung auf. Das ViewModel verlangt nur noch nach "irgendetwas, das Nachrichten anzeigen kann".

#### 2. Austauschbarkeit (Polymorphismus)
*   **Zur Laufzeit in der App:** Wir übergeben dem ViewModel den `AvaloniaDialogService`. Dieser zeigt echte Fenster an.
*   **Während des Unit Tests:** Wir übergeben dem ViewModel ein "Mock-Objekt" (eine Attrappe). Diese implementiert zwar das Interface, führt aber keinen UI-Code aus. Wenn das ViewModel `ShowMessageAsync` aufruft, passiert im Test einfach gar nichts – die Exception wird vermieden, und der Test kann ungehindert fortfahren.

#### 3. Testbarkeit der Logik
Durch das Interface können wir im Test prüfen, ob das ViewModel die richtige Entscheidung getroffen hat, ohne ein Fenster sehen zu müssen. Wir fragen den Mock einfach: *"Wurde deine ShowMessage-Methode mit dem Text 'Name leer' aufgerufen?"*. So testen wir die **Logik** (Validierung) getrennt von der **Darstellung** (UI).
