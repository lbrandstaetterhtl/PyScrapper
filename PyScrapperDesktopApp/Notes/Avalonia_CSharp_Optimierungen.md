# Avalonia / C# – nützliche Mittel mit kurzes Codebeispiel & Fundstellen

Diese Datei wurde erweitert: zu jedem Punkt ein kurzer Code-Ausschnitt aus dem Projekt, danach nur noch Datei:Zeile-Verweise.

---

## 1. Performance und Geschwindigkeit

- `async` / `await` — echtes Beispiel (aus `ApiClient.cs`):

```csharp
// Beispiel: sichere HTTP-POST mit CancellationToken und Stream-Deserialisierung
using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(60));
var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/download", content, cts.Token); // Verwendung von CancellationToken
response.EnsureSuccessStatusCode();
await using var stream = await response.Content.ReadAsStreamAsync(cts.Token); // effizienter als ReadAsStringAsync
var deserialized = await JsonSerializer.DeserializeAsync<NormalResponse>(stream, JsonOptions, cts.Token); // direkte Stream-Deserialisierung
var responseData = deserialized?.Message ?? string.Empty;
```

Weitere Fundstellen: `ApiClient.cs:32-64`, `72-116`, `125-150`, `163-257`; `App.axaml.cs:118-205`

- `CancellationToken` — sinnvoll z.B. in `ScanFolder` (Abbruchfähigkeit):

```csharp
// (empfohlen) Beispiel-Pattern mit CancellationToken
public async Task<int> ScanFolder(string folder, CancellationToken ct)
{
    ct.ThrowIfCancellationRequested(); // prüfe regelmäßig

    // Beispiel: asynchrone Enumeration mit CancellationToken
    await foreach (var file in Directory.EnumerateFiles(folder, "*", SearchOption.AllDirectories).ToAsyncEnumerable().WithCancellation(ct))
    {
        ct.ThrowIfCancellationRequested();
        // Beispiel: falls du Datei-IO asynchron machst, gib ct weiter
        var info = new FileInfo(file);
        // ... verarbeite Datei ...
    }

    return 0;
}

// Aufrufer-Beispiel:
// using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
// var added = await ScanFolder(downloadPath, cts.Token);
```

Weitere Stellen: `App.axaml.cs:244-307`; `ApiClient.cs:32-64`

- `Span<T>` / `Memory<T>` — Einsatz bei Byte-Arrays (Thumbnail/Stream-Verarbeitung):

```csharp
// Beispiel: Buffer Verarbeitung (konzeptionell)
var buffer = new ReadOnlyMemory<byte>(data);
ProcessBuffer(buffer.Span); // Verbesserung: Verwende Span<T>/Memory<T> in Parsern, um Kopien zu vermeiden und Garbage zu reduzieren

// Beispiel-Aufrufer:
// void ProcessBuffer(Span<byte> span) { /* parse ohne zu kopieren */ }
```

Weitere Stellen: `ApiClient.cs:125-150`, `163-257`

---

## 2. Avalonia-spezifisch

- `x:DataType` (Compiled bindings) — Beispiel aus `MainWindow.axaml`:

```xml
<Window ... x:DataType="vm:MainWindowViewModel">
  <!-- typed bindings sind hier aktiv -->
  <!-- Beispiel: <TextBlock Text="{Binding SelectedPlaylist.Name}"/> – mit x:DataType bekommst du Compiler-Warnungen, falls Name nicht existiert -->
</Window>
```

Fundstellen: `MainWindow.axaml:9-10`; `ScrapWindowWithSearch.axaml:8-9`; `FilterWindow.axaml:8-9`

- Virtualisierung / `ItemsControl` (Beispiel aus `MainWindow.axaml` — kann zu `VirtualizingStackPanel`/`ItemsRepeater` migriert werden):

```xml
<ItemsControl Grid.Row="2" ItemsSource="{Binding Playlists}">
  <ItemsControl.ItemsPanel>
    <ItemsPanelTemplate>
      <!-- Verbesserung: Ersetze hier durch VirtualizingStackPanel oder ItemsRepeater für Virtualisierung -->
      <VirtualizingStackPanel />
    </ItemsPanelTemplate>
  </ItemsControl.ItemsPanel>
  <ItemsControl.ItemTemplate>
    <DataTemplate>
      <!-- Item Template -->
    </DataTemplate>
  </ItemsControl.ItemTemplate>
</ItemsControl>

<!-- Nutzungshinweis: Wenn du VirtualizingStackPanel nutzt, stelle sicher, dass ItemsControl.VirtualizationMode=Recycling gesetzt ist -->
<!-- Beispiel: <ItemsControl VirtualizationMode="Recycling" .../> -->
```

Fundstellen: `MainWindow.axaml:108-138`, `171-217`; `ScrapWindowWithSearch.axaml:64-92`

- Thumbnail Caching — wo Thumbnails geladen werden (`ApiClient`):

```csharp
// Download und Setzen von ThumbnailBitmap in SearchResultItem
// Beispiel: prüfe Disk-Cache, lade falls nötig, speichere Disk- und Memory-Cache
var cacheKey = GetCacheKey(result.thumbnail);
var cachePath = Path.Combine(AppData.DataPath, "thumbnails", cacheKey + ".png");
if (File.Exists(cachePath))
{
    result.ThumbnailBitmap = new Bitmap(cachePath); // lade vom Disk-Cache
}
else
{
    using var thumbResponse = await client.GetAsync(result.thumbnail, CancellationToken.None); // Improvement: pass CancellationToken
    var imageData = await thumbResponse.Content.ReadAsByteArrayAsync();
    Directory.CreateDirectory(Path.GetDirectoryName(cachePath)!);
    await File.WriteAllBytesAsync(cachePath, imageData);
    result.ThumbnailBitmap = new Bitmap(new MemoryStream(imageData));
    // optional: store in in-memory dictionary for faster access
}
```

Fundstellen: `ApiClient.cs:125-150`, `292-299`

---

## 3. Sicherheit & Stabilität

- `using` / `await using` — echtes Beispiel (`App.axaml.cs` StopServer):

```csharp
using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
try
{
    using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(3));
    await http.PostAsync("http://127.0.0.1:8765/command", new StringContent("{\"command\":\"quit\"}", Encoding.UTF8, "application/json"), cts.Token);
}
catch (Exception ex)
{
    // Server might be down — log and ignore
}
```

Weitere Stellen: `App.axaml.cs:325-339`; `AppLogger.cs:18-31`; `ApiClient.cs:32-64`

- `Path.Combine` — Beispiel aus `AppData.cs`:

```csharp
public static string AppLogsPath { get; set; } = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "logs"); // Verbesserung: Validiere und erstelle den Ordner beim Start (Directory.CreateDirectory)
// Beispiel beim Start:
// Directory.CreateDirectory(AppLogsPath);
```

Weitere Stellen: `AppData.cs:27-31`; `AppLogger.cs:20-31`

- `Dispatcher.UIThread.InvokeAsync` — echtes Beispiel (`CodecConverterWindowViewModel`):

```csharp
try
{
    await Dispatcher.UIThread.InvokeAsync(() =>
    {
        ProgressValue = progress;
        StatusMessage = $"Converting... {ProgressValue:F2}%";
    });
}
catch (Exception)
{
    // View might be closed — ignore or log
}
// Verbesserung: Wrappe UI-Update in try/catch falls View bereits geschlossen ist; nutze ConfigureAwait(false) in non-UI code
```

Fundstellen: `ViewModels/CodecConverterWindowViewModel.cs:144-149`, `153-159`, `171-175`

---

## 4. Nützliche Libraries

- `CommunityToolkit.Mvvm` — sehr präsent (`[ObservableProperty]`, `[RelayCommand]`): see `ViewModels/*` (z.B. `CodecConverterWindowViewModel.cs:26-36`)
- `System.Text.Json` — DTO-Serialisierung: `ServerRequestData.cs`, `ServerResponses.cs`, `ApiClient.cs`
- `Polly` — empfehlenswert für HTTP-Retries around `ApiClient` calls
- `Microsoft.Extensions.DependencyInjection` — geeignet für DI in `App.axaml.cs`

---

## 5. Sofort-Umsetzungs-Priorität (Kurz)

1. Thumbnail-Caching — implementieren an `ApiClient` (wo Thumbnails gesetzt werden)
2. Virtualisierung großer Listen — `MainWindow.axaml` ItemsControls → Virtualizing/ItemsRepeater
3. `CancellationToken` bei `ScanFolder` & API-Calls — `App.axaml.cs:244-307`, `ApiClient.cs`

---

Wenn du willst, erstelle ich die PR-Patches für die Top-3 Änderungen (Thumbnail cache, Virtualizing switch, CancellationToken) und teste sie lokal.


