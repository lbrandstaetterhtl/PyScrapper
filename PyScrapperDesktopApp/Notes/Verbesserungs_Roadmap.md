# PyScrapper - Verbesserungs-Roadmap & Aufgabenliste

## Task-Tabelle

| # | Task | Priorität | Aufwand | Status | Sprint | Abhängigkeiten |
|---|------|-----------|---------|--------|--------|-----------------|
| 1 | GetInstance() Pattern für AppData - nicht statisch | 🔴 High | 2-3 Tage | TODO | S1 | - |
| 2 | Unit Tests schreiben (Filter, AudioPlayer, MediaFilter) | 🔴 High | 3-4 Tage | TODO | S1 | Task 1 |
| 3 | Thumbnail Caching System implementieren | 🔴 High | 1-2 Tage | TODO | S1 | - |
| 4 | Refactor große ViewModels (MainWindowViewModel splitten) | 🟠 Medium | 2-3 Tage | TODO | S2 | - |
| 5 | Performance: Pagination für Media-Listen | 🟠 Medium | 2-3 Tage | TODO | S2 | Task 4 |
| 6 | Undo/Redo System für Delete-Operationen | 🟠 Medium | 3-4 Tage | TODO | S2 | Task 1 |
| 7 | MDI oder Tab-based Window System | 🟡 Low | 5-7 Tage | TODO | S3 | Task 4 |
| 8 | Theme Editor / Customization UI | 🟡 Low | 2-3 Tage | TODO | S3 | - |
| 9 | Advanced Search (Regex Support) | 🟡 Low | 1-2 Tage | TODO | S3 | - |

---

## Detaillierte Aufgabenbeschreibungen mit Beispielen

---

### 1. 🔴 GetInstance() Pattern für AppData - nicht statisch

#### Erklärung
**Problem:** AppData ist aktuell eine statische Klasse:
```csharp
public static class AppData { ... }
```
Das macht das Testing unmöglich, da man Singletons nicht mocken kann. Unit-Tests können die Daten nicht isolieren.

**Lösung:** Implementiere das **GetInstance() Singleton Pattern** oder nutze **Dependency Injection** mit einer Schnittstelle `IAppData`.

#### Beispiel - Vorher (Statisch, nicht testbar):
```csharp
// ❌ AKTUELLER CODE (nicht testbar)
public static class AppData
{
    public static ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static ObservableCollection<Playlist> Playlists = new();
}

// In ViewModel:
public class MainWindowViewModel
{
    public void LoadData()
    {
        foreach (var media in AppData.DownloadedMedias) // ❌ Direkt static - nicht mockbar
        {
            // ...
        }
    }
}

// ❌ Unit Test - UNMÖGLICH
[Test]
public void TestFilterWithEmptyData()
{
    // Kann AppData.DownloadedMedias nicht zur Testzweck-Kontrolle setzen
    // Alle Tests beeinflussen sich gegenseitig
}
```

#### Beispiel - Nachher (Dependency Injection, testbar):
```csharp
// ✓ INTERFACE definieren
public interface IAppData
{
    ObservableCollection<DownloadedMedia> DownloadedMedias { get; }
    ObservableCollection<Playlist> Playlists { get; }
    Settings Settings { get; }
    void AddDownloadedMedia(DownloadedMedia media);
    bool MediaAlreadyExists(string filePath);
}

// ✓ IMPLEMENTIERUNG
public class AppData : IAppData
{
    private static readonly Lazy<AppData> _instance = new(() => new AppData());
    public static AppData Instance => _instance.Value;
    
    public ObservableCollection<DownloadedMedia> DownloadedMedias { get; } = new();
    public ObservableCollection<Playlist> Playlists { get; } = new();
    public Settings Settings { get; set; } = new();
    
    public void AddDownloadedMedia(DownloadedMedia media)
    {
        DownloadedMedias.Add(media);
    }
    
    public bool MediaAlreadyExists(string filePath)
    {
        return DownloadedMedias.Any(m => m.DownloadPath == filePath);
    }
}

// ✓ In ViewModel - Dependency Injection
public class MainWindowViewModel
{
    private readonly IAppData _appData;
    
    // Constructor Injection
    public MainWindowViewModel(IAppData appData)
    {
        _appData = appData;
    }
    
    public void LoadData()
    {
        foreach (var media in _appData.DownloadedMedias) // ✓ Injiziert, leicht zu mocken
        {
            // ...
        }
    }
}

// ✓ Unit Test - MÖGLICH und SAUBER
[TestFixture]
public class FilterTests
{
    private Mock<IAppData> _mockAppData;
    private MediaFilter _filter;
    
    [SetUp]
    public void Setup()
    {
        _mockAppData = new Mock<IAppData>();
        _filter = new MediaFilter();
    }
    
    [Test]
    public void TestFilterWithEmptyData()
    {
        // ARRANGE - Vollständige Kontrolle über Test-Daten
        var emptyCollection = new ObservableCollection<DownloadedMedia>();
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(emptyCollection);
        
        // ACT
        var result = _filter.ApplyMediaFilter(_mockAppData.Object, "test");
        
        // ASSERT
        Assert.That(result.Count, Is.EqualTo(0));
    }
    
    [Test]
    public void TestFilterWithData()
    {
        // ARRANGE - Genau definierte Test-Daten
        var media = new DownloadedMedia(
            url: "http://example.com",
            mediaType: ".mp4",
            downloadedAt: DateTime.Now,
            downloadPath: "/path/file.mp4",
            isPlayable: true,
            identifier: "test123"
        ) { Title = "Test Song" };
        
        var collection = new ObservableCollection<DownloadedMedia> { media };
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(collection);
        
        // ACT
        var result = _filter.ApplyMediaFilter(_mockAppData.Object, "Test");
        
        // ASSERT
        Assert.That(result.Count, Is.EqualTo(1));
        Assert.That(result[0].Title, Is.EqualTo("Test Song"));
    }
}

// ✓ App.axaml.cs - DI Container Setup
public override void OnFrameworkInitializationCompleted()
{
    var services = new ServiceCollection();
    
    // Registriere alle Dependencies
    services.AddSingleton<IAppData>(AppData.Instance);
    services.AddSingleton<IApiClient, ApiClient>();
    services.AddSingleton<IAppLogger, AppLogger>();
    services.AddSingleton<IStorageService, StorageService>();
    
    // ViewModels mit Dependency Injection
    services.AddTransient<MainWindowViewModel>();
    services.AddTransient<ScrapWindowWithSearchViewModel>();
    services.AddTransient<FilterWindowViewModel>();
    
    var serviceProvider = services.BuildServiceProvider();
    
    if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
    {
        desktop.MainWindow = new MainWindow
        {
            DataContext = serviceProvider.GetRequiredService<MainWindowViewModel>()
        };
    }
    
    base.OnFrameworkInitializationCompleted();
}
```

#### Vorteil:
- ✓ Unit Tests unabhängig voneinander
- ✓ Jeder Test mit isolierten Daten
- ✓ Mock-Objekte statt echte Dependencies
- ✓ Schnellere Tests (kein DB/API Zugriff)

---

### 2. 🔴 Unit Tests schreiben (Filter, AudioPlayer, MediaFilter)

#### Erklärung
**Problem:** Keine Unit Tests bedeutet: Jeden Bug manuell testen, Regression-Testing unmöglich

**Lösung:** Schreibe Tests für die 3 kritischsten Komponenten:
- MediaFilter (komplexe Logik)
- AudioPlayer (State Machine)
- ApiClient (Fehlerbehandlung)

#### Beispiel - MediaFilter Tests

```csharp
[TestFixture]
public class MediaFilterTests
{
    private Mock<IAppData> _mockAppData;
    private MediaFilter _filter;
    
    [SetUp]
    public void Setup()
    {
        _mockAppData = new Mock<IAppData>();
        _filter = new MediaFilter();
    }
    
    // TEST 1: Filter mit Search Query
    [Test]
    public void ApplyFilter_WithSearchQuery_ReturnsMatchingItems()
    {
        // ARRANGE
        var media1 = new DownloadedMedia("url", ".mp4", DateTime.Now, "path1", true, "id1") 
            { Title = "Lofi Beats" };
        var media2 = new DownloadedMedia("url", ".mp3", DateTime.Now, "path2", true, "id2") 
            { Title = "Heavy Metal" };
        
        var collection = new ObservableCollection<DownloadedMedia> { media1, media2 };
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(collection);
        
        var filter = new MediaFilter { SearchQuery = "Lofi" };
        
        // ACT
        var result = MediaFilter.ApplyMediaFilter(_mockAppData.Object, filter);
        
        // ASSERT
        Assert.That(result.Count, Is.EqualTo(1));
        Assert.That(result[0].Title, Contains.Substring("Lofi"));
    }
    
    // TEST 2: Filter mit MediaType
    [Test]
    public void ApplyFilter_WithMediaType_OnlyReturnsMp4()
    {
        // ARRANGE
        var media1 = new DownloadedMedia("url", ".mp4", DateTime.Now, "path1", true, "id1") 
            { Title = "Video" };
        var media2 = new DownloadedMedia("url", ".mp3", DateTime.Now, "path2", true, "id2") 
            { Title = "Audio" };
        
        var collection = new ObservableCollection<DownloadedMedia> { media1, media2 };
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(collection);
        
        var mediaTypes = new ObservableCollection<string> { ".mp4" };
        var filter = new MediaFilter { MediaTypes = mediaTypes };
        
        // ACT
        var result = MediaFilter.ApplyMediaFilter(_mockAppData.Object, filter);
        
        // ASSERT
        Assert.That(result.Count, Is.EqualTo(1));
        Assert.That(result[0].MediaType, Is.EqualTo(".mp4"));
    }
    
    // TEST 3: Filter mit Date Range
    [Test]
    public void ApplyFilter_WithDateRange_OnlyReturnsItemsInRange()
    {
        // ARRANGE
        var today = DateTime.Now;
        var media1 = new DownloadedMedia("url", ".mp4", today.AddDays(-5), "path1", true, "id1") 
            { Title = "Old" };
        var media2 = new DownloadedMedia("url", ".mp4", today, "path2", true, "id2") 
            { Title = "New" };
        var media3 = new DownloadedMedia("url", ".mp4", today.AddDays(5), "path3", true, "id3") 
            { Title = "Future" };
        
        var collection = new ObservableCollection<DownloadedMedia> { media1, media2, media3 };
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(collection);
        
        var filter = new MediaFilter 
        { 
            StartDate = today.AddDays(-1).ToDateTimeOffset(),
            EndDate = today.AddDays(1).ToDateTimeOffset()
        };
        
        // ACT
        var result = MediaFilter.ApplyMediaFilter(_mockAppData.Object, filter);
        
        // ASSERT
        Assert.That(result.Count, Is.GreaterThanOrEqualTo(1));
        Assert.That(result.All(m => m.DownloadedAt >= today.AddDays(-1)), Is.True);
    }
    
    // TEST 4: Filter mit Combined Criteria
    [Test]
    public void ApplyFilter_WithMultipleCriteria_OnlyReturnsCompleteMatch()
    {
        // ARRANGE
        var today = DateTime.Now;
        var media1 = new DownloadedMedia("url", ".mp4", today, "path1", true, "id1") 
            { Title = "Lofi Video" };
        var media2 = new DownloadedMedia("url", ".mp3", today, "path2", true, "id2") 
            { Title = "Lofi Music" };
        var media3 = new DownloadedMedia("url", ".mp4", today, "path3", false, "id3") 
            { Title = "Lofi Podcast" };
        
        var collection = new ObservableCollection<DownloadedMedia> { media1, media2, media3 };
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(collection);
        
        var filter = new MediaFilter 
        { 
            SearchQuery = "Lofi",
            MediaTypes = new ObservableCollection<string> { ".mp4" },
            IsPlayable = true  // Nur spielbare Medien
        };
        
        // ACT
        var result = MediaFilter.ApplyMediaFilter(_mockAppData.Object, filter);
        
        // ASSERT - NUR media1 sollte passen (Video, Lofi, Playable)
        Assert.That(result.Count, Is.EqualTo(1));
        Assert.That(result[0].Title, Is.EqualTo("Lofi Video"));
    }
    
    // TEST 5: Clear Filter
    [Test]
    public void ClearFilter_RestoresOriginalCollection()
    {
        // ARRANGE
        var media1 = new DownloadedMedia("url", ".mp4", DateTime.Now, "path1", true, "id1");
        var media2 = new DownloadedMedia("url", ".mp3", DateTime.Now, "path2", true, "id2");
        
        var original = new ObservableCollection<DownloadedMedia> { media1, media2 };
        var filtered = new ObservableCollection<DownloadedMedia> { media1 };
        
        _mockAppData.Setup(a => a.DownloadedMedias).Returns(filtered);
        
        // ACT
        MediaFilter.ClearFilter(_mockAppData.Object, original);
        
        // ASSERT
        Assert.That(filtered.Count, Is.EqualTo(2));
    }
}
```

#### Test-Ausführung
```bash
# Unit Tests mit NUnit Runner
dotnet test PyScrapperDesktopApp.Tests

# Output:
# ✓ ApplyFilter_WithSearchQuery_ReturnsMatchingItems PASSED
# ✓ ApplyFilter_WithMediaType_OnlyReturnsMp4 PASSED
# ✓ ApplyFilter_WithDateRange_OnlyReturnsItemsInRange PASSED
# ✓ ApplyFilter_WithMultipleCriteria_OnlyReturnsCompleteMatch PASSED
# ✓ ClearFilter_RestoresOriginalCollection PASSED
# 
# Test Run Successful. 5 passed in 245ms
```

---

### 3. 🔴 Thumbnail Caching System implementieren

#### Erklärung
**Problem:** Jedes Mal wenn der User in die ScrapWindowWithSearch geht, werden alle Thumbnails NEU heruntergeladen von den Servern.
- Langsam (50 Videos = 50 HTTP-Requests)
- Verschwendet Bandwidth
- Schlecht UX (Wartezeit)

**Lösung:** Cache Thumbnails lokal im AppData-Ordner mit Filename-Hash als Key.

#### Beispiel - Caching Implementation

```csharp
// ✗ AKTUELLER CODE (KEIN CACHE)
public async Task<List<SearchResultItem>> SendSearchRequest(SearchRequestData requestData)
{
    var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/search", content);
    var results = JsonSerializer.Deserialize<SearchSuccessResponse>(response.Content);
    
    // ❌ JEDES MAL: Alle Thumbnails herunterladen
    foreach (var result in results.Results)
    {
        using (var thumbResponse = await client.GetAsync(result.thumbnail))
        {
            var imageData = await thumbResponse.Content.ReadAsByteArrayAsync();
            result.ThumbnailBitmap = new Bitmap(new MemoryStream(imageData));
        }
    }
    
    return results.Results;
}

// ✓ VERBESSERTER CODE (MIT CACHE)
public class ThumbnailCache
{
    private readonly string _cacheDirectory;
    private readonly Dictionary<string, Bitmap> _memoryCache = new();
    
    public ThumbnailCache()
    {
        _cacheDirectory = Path.Combine(AppData.DataPath, "thumbnails");
        if (!Directory.Exists(_cacheDirectory))
            Directory.CreateDirectory(_cacheDirectory);
    }
    
    // Cache-Key aus URL generieren (MD5 Hash)
    private string GetCacheKey(string url)
    {
        using (var md5 = System.Security.Cryptography.MD5.Create())
        {
            var hash = md5.ComputeHash(Encoding.UTF8.GetBytes(url));
            return BitConverter.ToString(hash).Replace("-", "").ToLower();
        }
    }
    
    public async Task<Bitmap> GetThumbnailAsync(string url, HttpClient client)
    {
        var cacheKey = GetCacheKey(url);
        
        // SCHRITT 1: Prüfe Memory Cache (schnellste Option)
        if (_memoryCache.ContainsKey(cacheKey))
        {
            Console.WriteLine($"✓ Thumbnail aus Memory Cache: {cacheKey}");
            return _memoryCache[cacheKey];
        }
        
        // SCHRITT 2: Prüfe Disk Cache
        var diskCachePath = Path.Combine(_cacheDirectory, $"{cacheKey}.png");
        if (File.Exists(diskCachePath))
        {
            Console.WriteLine($"✓ Thumbnail aus Disk Cache: {cacheKey}");
            var bitmap = new Bitmap(diskCachePath);
            _memoryCache[cacheKey] = bitmap; // Auch ins Memory Cache
            return bitmap;
        }
        
        // SCHRITT 3: Download vom Server und Cache
        Console.WriteLine($"⬇️ Thumbnail wird heruntergeladen: {url}");
        try
        {
            using (var response = await client.GetAsync(url))
            {
                var imageData = await response.Content.ReadAsByteArrayAsync();
                
                // Speichere auf Disk
                await File.WriteAllBytesAsync(diskCachePath, imageData);
                
                // Lade ins Memory
                var bitmap = new Bitmap(new MemoryStream(imageData));
                _memoryCache[cacheKey] = bitmap;
                
                Console.WriteLine($"✓ Thumbnail gesendet und gecacht: {cacheKey}");
                return bitmap;
            }
        }
        catch (Exception ex)
        {
            AppLogger.LogNewMassage(new Massage($"Fehler beim Cache-Download: {ex.Message}", DateTime.Now, "ERROR"));
            return null;
        }
    }
    
    // Cache-Statistiken
    public void PrintCacheStats()
    {
        var diskFiles = Directory.GetFiles(_cacheDirectory).Length;
        Console.WriteLine($"📊 Cache-Statistiken:");
        Console.WriteLine($"   Memory Cache: {_memoryCache.Count} Items");
        Console.WriteLine($"   Disk Cache: {diskFiles} Files");
    }
    
    // Cache Cleanup (optional - für alte Dateien)
    public void CleanupOldCache(int daysOld = 30)
    {
        var cutoffDate = DateTime.Now.AddDays(-daysOld);
        foreach (var file in Directory.GetFiles(_cacheDirectory))
        {
            var fileInfo = new FileInfo(file);
            if (fileInfo.LastAccessTime < cutoffDate)
            {
                fileInfo.Delete();
                Console.WriteLine($"🗑️ Alt Cache gelöscht: {fileInfo.Name}");
            }
        }
    }
}

// ✓ VERWENDUNG IN ApiClient
public class ApiClient : IApiClient
{
    private readonly ThumbnailCache _thumbnailCache;
    
    public ApiClient()
    {
        _thumbnailCache = new ThumbnailCache();
    }
    
    public async Task<List<SearchResultItem>> SendSearchRequest(SearchRequestData requestData)
    {
        HttpClient client = new();
        
        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/search", content);
        
        var results = JsonSerializer.Deserialize<SearchSuccessResponse>(await response.Content.ReadAsStringAsync());
        
        // ✓ Mit Cache herunterladen
        foreach (var result in results.Results)
        {
            result.ThumbnailBitmap = await _thumbnailCache.GetThumbnailAsync(result.thumbnail, client);
        }
        
        return results.Results;
    }
}

// ✓ Disk Cache Directory Struktur
// AppData/data/
//   └─ thumbnails/
//      ├─ 3a2b1c4d5e6f7g8h9i0j.png (50 KB)
//      ├─ 1x2y3z4a5b6c7d8e9f0g.png (48 KB)
//      └─ 5m6n7o8p9q0r1s2t3u4v.png (52 KB)

// ✓ Performance Vergleich
// Vor Cache:     50 Videos × 500ms Download = 25 Sekunden ⏱️❌
// Mit Cache:     1. Run: 25s, 2. Run: <100ms ⚡✓
```

---

### 4. 🟠 Refactor große ViewModels (MainWindowViewModel splitten)

#### Erklärung
**Problem:** MainWindowViewModel hat zu viele Verantwortlichkeiten:
- Playlist Management
- Media List Management
- Sorting/Filtering
- Filter Window Logic
- Delete Operations
- Context Menu Handlers

Besser: Es sollte mehrere kleinere ViewModels geben.

#### Beispiel - Vorher vs. Nachher

```csharp
// ❌ JETZT: MainWindowViewModel hat ALLES
public class MainWindowViewModel
{
    [ObservableProperty] private ObservableCollection<Playlist> playlists;
    [ObservableProperty] private ObservableCollection<DownloadedMedia> downloadedMediaList;
    [ObservableProperty] private Playlist selectedPlaylist;
    [ObservableProperty] private DownloadedMedia selectedMedia;
    
    // 50+ Commands
    [RelayCommand] public async Task SortByName() { ... }
    [RelayCommand] public async Task SortByDate() { ... }
    [RelayCommand] public async Task SortById() { ... }
    [RelayCommand] public async Task FilterClick() { ... }
    [RelayCommand] public async Task ClearFilter() { ... }
    [RelayCommand] public async Task DeleteMedia(DownloadedMedia media) { ... }
    [RelayCommand] public async Task DeletePlaylist(Playlist playlist) { ... }
    [RelayCommand] public async Task PlaylistDoubleClick(Playlist playlist) { ... }
    [RelayCommand] public async Task MediaDoubleClick(DownloadedMedia media) { ... }
    [RelayCommand] public async Task AddToPlaylist(DownloadedMedia media, Playlist playlist) { ... }
    // ... 15+ more commands
}

// ✓ NACHHER: Aufgeteilt in spezialisierte ViewModels
public interface IMediaListViewModel
{
    ObservableCollection<DownloadedMedia> DownloadedMediaList { get; }
    IAsyncRelayCommand<DownloadedMedia> DeleteMediaCommand { get; }
    IAsyncRelayCommand<DownloadedMedia> PlayMediaCommand { get; }
}

public class MediaListViewModel : ObservableObject, IMediaListViewModel
{
    private readonly IAppData _appData;
    private readonly IApiClient _apiClient;
    private readonly IAudioPlayer _audioPlayer;
    
    [ObservableProperty]
    private ObservableCollection<DownloadedMedia> downloadedMediaList;
    
    [RelayCommand]
    public async Task DeleteMedia(DownloadedMedia media)
    {
        if (MessageBox.ShowConfirmation("Delete this media?"))
        {
            _appData.RemoveDownloadedMedia(media);
            await DatabaseOperations.SaveDownloadedMedias(_appData.DownloadedMedias);
        }
    }
    
    [RelayCommand]
    public async Task PlayMedia(DownloadedMedia media)
    {
        await _audioPlayer.LoadMedia(media);
    }
}

public interface IPlaylistViewModel
{
    ObservableCollection<Playlist> Playlists { get; }
    IAsyncRelayCommand<Playlist> DeletePlaylistCommand { get; }
    IAsyncRelayCommand<Playlist> ViewPlaylistDetailsCommand { get; }
}

public class PlaylistViewModel : ObservableObject, IPlaylistViewModel
{
    private readonly IAppData _appData;
    
    [ObservableProperty]
    private ObservableCollection<Playlist> playlists;
    
    [RelayCommand]
    public async Task DeletePlaylist(Playlist playlist)
    {
        if (MessageBox.ShowConfirmation($"Delete playlist '{playlist.Name}'?"))
        {
            _appData.RemovePlaylist(playlist);
            await DatabaseOperations.SavePlaylists(_appData.Playlists);
        }
    }
    
    [RelayCommand]
    public async Task ViewPlaylistDetails(Playlist playlist)
    {
        var viewModel = new PlaylistDetailsWindowViewModel(playlist, _appData);
        var window = new PlaylistDetailsWindow { DataContext = viewModel };
        await window.ShowDialog();
    }
}

public interface ISortFilterViewModel
{
    IAsyncRelayCommand SortByNameCommand { get; }
    IAsyncRelayCommand SortByDateCommand { get; }
    IAsyncRelayCommand OpenFilterCommand { get; }
    IAsyncRelayCommand ClearFilterCommand { get; }
}

public class SortFilterViewModel : ObservableObject, ISortFilterViewModel
{
    private readonly IAppData _appData;
    
    [RelayCommand]
    public async Task SortByName()
    {
        var sorted = new ObservableCollection<DownloadedMedia>(
            _appData.DownloadedMedias.OrderBy(m => m.Title)
        );
        _appData.DownloadedMedias.Clear();
        foreach (var item in sorted) _appData.DownloadedMedias.Add(item);
    }
    
    [RelayCommand]
    public async Task SortByDate()
    {
        var sorted = new ObservableCollection<DownloadedMedia>(
            _appData.DownloadedMedias.OrderByDescending(m => m.DownloadedAt)
        );
        _appData.DownloadedMedias.Clear();
        foreach (var item in sorted) _appData.DownloadedMedias.Add(item);
    }
    
    [RelayCommand]
    public async Task OpenFilter()
    {
        var viewModel = new FilterWindowViewModel(_appData);
        var window = new FilterWindow { DataContext = viewModel };
        await window.ShowDialog();
    }
    
    [RelayCommand]
    public async Task ClearFilter()
    {
        await MediaFilter.ClearFilter(_appData);
    }
}

// ✓ NEUE MainWindowViewModel - Nur noch Orchestration
public class MainWindowViewModel : ObservableObject
{
    public IMediaListViewModel MediaListViewModel { get; }
    public IPlaylistViewModel PlaylistViewModel { get; }
    public ISortFilterViewModel SortFilterViewModel { get; }
    
    public MainWindowViewModel(
        IMediaListViewModel mediaListViewModel,
        IPlaylistViewModel playlistViewModel,
        ISortFilterViewModel sortFilterViewModel)
    {
        MediaListViewModel = mediaListViewModel;
        PlaylistViewModel = playlistViewModel;
        SortFilterViewModel = sortFilterViewModel;
    }
}

// ✓ XAML wird auch sauberer
<Grid>
    <!-- Playlists Section -->
    <ContentControl Content="{Binding PlaylistViewModel}" />
    
    <!-- Sort/Filter Section -->
    <ContentControl Content="{Binding SortFilterViewModel}" />
    
    <!-- Media List Section -->
    <ContentControl Content="{Binding MediaListViewModel}" />
</Grid>
```

---

### 5. 🟠 Performance: Pagination für Media-Listen

#### Erklärung
**Problem:** Wenn der User 50.000 Medien hat, lädt MainWindow **alle 50.000** und rendert die UI.
- Langsam (UI-Freeze)
- Hoher RAM-Verbrauch
- Scrolling laggy

**Lösung:** Implementiere **Virtualization** + **Pagination**: Lade nur 50 Items, beim Scrollen lade nächste 50.

#### Beispiel - Pagination Implementation

```csharp
// ✓ Pagination Service
public interface IPagedCollectionService
{
    IAsyncRelayCommand<int> LoadPageCommand { get; }
    ObservableCollection<DownloadedMedia> CurrentPageItems { get; }
    int CurrentPageIndex { get; }
    int PageSize { get; }
    int TotalPages { get; }
}

public class PagedCollectionService : ObservableObject, IPagedCollectionService
{
    private readonly IAppData _appData;
    private const int DEFAULT_PAGE_SIZE = 50;
    
    [ObservableProperty] private int pageSize = DEFAULT_PAGE_SIZE;
    [ObservableProperty] private int currentPageIndex = 0;
    [ObservableProperty] private int totalPages;
    [ObservableProperty] private ObservableCollection<DownloadedMedia> currentPageItems;
    
    public PagedCollectionService(IAppData appData)
    {
        _appData = appData;
        currentPageItems = new();
        UpdateTotalPages();
    }
    
    [RelayCommand]
    public async Task LoadPage(int pageIndex)
    {
        if (pageIndex < 0 || pageIndex >= TotalPages)
            return;
        
        CurrentPageIndex = pageIndex;
        
        // BERECHNE welche Items diese Seite braucht
        var startIndex = pageIndex * PageSize;
        var endIndex = Math.Min(startIndex + PageSize, _appData.DownloadedMedias.Count);
        
        // LADE nur diese Items
        var pageItems = _appData.DownloadedMedias
            .Skip(startIndex)
            .Take(PageSize)
            .ToList();
        
        // UPDATE UI Collection
        CurrentPageItems.Clear();
        foreach (var item in pageItems)
        {
            CurrentPageItems.Add(item);
        }
    }
    
    private void UpdateTotalPages()
    {
        TotalPages = (int)Math.Ceiling((double)_appData.DownloadedMedias.Count / PageSize);
        if (TotalPages > 0)
            LoadPage(0); // Lade erste Seite
    }
    
    // Pagination Controls für UI
    public void NextPage()
    {
        if (CurrentPageIndex < TotalPages - 1)
            LoadPage(CurrentPageIndex + 1);
    }
    
    public void PreviousPage()
    {
        if (CurrentPageIndex > 0)
            LoadPage(CurrentPageIndex - 1);
    }
    
    public void GoToPage(int pageIndex)
    {
        LoadPage(pageIndex);
    }
}

// ✓ XAML mit Virtualisierung
<Grid>
    <ScrollViewer>
        <ItemsControl ItemsSource="{Binding CurrentPageItems}">
            <ItemsControl.ItemsPanel>
                <ItemsPanelTemplate>
                    <VirtualizingStackPanel />
                </ItemsPanelTemplate>
            </ItemsControl.ItemsPanel>
            
            <ItemsControl.ItemTemplate>
                <DataTemplate>
                    <Border Classes="MediaItem" Padding="10">
                        <StackPanel>
                            <TextBlock Text="{Binding Title}" FontWeight="Bold" />
                            <TextBlock Text="{Binding MediaType}" />
                        </StackPanel>
                    </Border>
                </DataTemplate>
            </ItemsControl.ItemTemplate>
        </ItemsControl>
    </ScrollViewer>
    
    <!-- Pagination Controls -->
    <StackPanel Orientation="Horizontal" HorizontalAlignment="Center" Margin="0,10">
        <Button Content="◀ Prev" Command="{Binding PaginationService.PreviousPageCommand}" />
        <TextBlock Text="{Binding PaginationService.CurrentPageIndex, StringFormat='Page {0}'}" Margin="10,0" VerticalAlignment="Center" />
        <TextBlock Text="{Binding PaginationService.TotalPages, StringFormat='of {0}'}" Margin="0,0,10,0" VerticalAlignment="Center" />
        <Button Content="Next ▶" Command="{Binding PaginationService.NextPageCommand}" />
    </StackPanel>
</Grid>

// ✓ Performance Vergleich
// Ohne Pagination:   50.000 Items laden + rendern = 5-10 Sekunden ❌
// Mit Pagination:    50 Items laden + rendern = <100ms ✓
// Beim Scrollen:     Nächste 50 automatisch geladen ✓
```

---

### 6. 🟠 Undo/Redo System für Delete-Operationen

#### Erklärung
**Problem:** User klickt versehentlich "Delete Playlist" und die Playlist ist weg (aber noch in DB).
Es gibt keinen Undo.

**Lösung:** Implementiere Command Pattern für Undo/Redo:

```csharp
// ✓ Command Pattern für Undo/Redo
public interface ICommand
{
    void Execute();
    void Undo();
    string Description { get; }
}

public class DeleteMediaCommand : ICommand
{
    private readonly IAppData _appData;
    private readonly DownloadedMedia _media;
    private readonly int _originalIndex;
    
    public string Description => $"Delete media '{_media.Title}'";
    
    public DeleteMediaCommand(IAppData appData, DownloadedMedia media)
    {
        _appData = appData;
        _media = media;
        // Merke ursprüngliche Position
        _originalIndex = _appData.DownloadedMedias.IndexOf(media);
    }
    
    public void Execute()
    {
        _appData.RemoveDownloadedMedia(_media);
    }
    
    public void Undo()
    {
        // Füge an ursprünglicher Position wieder ein
        _appData.DownloadedMedias.Insert(_originalIndex, _media);
    }
}

// ✓ Command History Manager
public class CommandHistory
{
    private Stack<ICommand> _undoStack = new();
    private Stack<ICommand> _redoStack = new();
    
    public event Action<string> OnCommandExecuted; // Für UI-Updates
    
    public void Execute(ICommand command)
    {
        command.Execute();
        _undoStack.Push(command);
        _redoStack.Clear(); // Bei neuem Befehl Redo-History löschen
        OnCommandExecuted?.Invoke($"✓ {command.Description}");
    }
    
    public void Undo()
    {
        if (_undoStack.Count == 0) return;
        
        var command = _undoStack.Pop();
        command.Undo();
        _redoStack.Push(command);
        OnCommandExecuted?.Invoke($"↶ Undo: {command.Description}");
    }
    
    public void Redo()
    {
        if (_redoStack.Count == 0) return;
        
        var command = _redoStack.Pop();
        command.Execute();
        _undoStack.Push(command);
        OnCommandExecuted?.Invoke($"↷ Redo: {command.Description}");
    }
}

// ✓ ViewModel Verwendung
public class MediaListViewModel : ObservableObject
{
    private readonly CommandHistory _commandHistory;
    
    [RelayCommand]
    public async Task DeleteMedia(DownloadedMedia media)
    {
        var command = new DeleteMediaCommand(_appData, media);
        _commandHistory.Execute(command);
    }
    
    [RelayCommand]
    public void Undo() => _commandHistory.Undo();
    
    [RelayCommand]
    public void Redo() => _commandHistory.Redo();
}

// ✓ UI mit Undo/Redo Buttons
<StackPanel Orientation="Horizontal">
    <Button Content="↶ Undo (Ctrl+Z)" Command="{Binding UndoCommand}" />
    <Button Content="↷ Redo (Ctrl+Y)" Command="{Binding RedoCommand}" />
</StackPanel>

// ✓ Demo
// 1. User klickt "Delete" auf Playlist "Favorites"
//    → Favorites wird gelöscht, CommandHistory.Push(DeleteCommand)
// 2. User drückt Ctrl+Z
//    → Favorites Kommt wieder, ist in Redo-Stack
// 3. User drückt Ctrl+Y
//    → Favorites wird wieder gelöscht
```

---

### 7. 🟡 MDI oder Tab-based Window System

#### Erklärung
**Problem:** Es gibt 14 separate Dialog-Windows. Navigation ist chaotisch.

**Lösung:** Multiple Document Interface (MDI) oder Tab-System für besseres Fenster-Management.

```csharp
// ✓ Tab-based Window System
<Grid ColumnDefinitions="*" RowDefinitions="Auto,*,Auto">
    
    <!-- TAB HEADER -->
    <ItemsControl Grid.Row="0" ItemsSource="{Binding OpenTabs}">
        <ItemsControl.ItemsPanel>
            <ItemsPanelTemplate>
                <StackPanel Orientation="Horizontal" />
            </ItemsPanelTemplate>
        </ItemsControl.ItemsPanel>
        
        <ItemsControl.ItemTemplate>
            <DataTemplate>
                <Border Classes="TabButton" 
                        Background="{Binding IsActive, Converter=...}"
                        Padding="12,8">
                    <StackPanel Orientation="Horizontal" Spacing="8">
                        <TextBlock Text="{Binding Title}" />
                        <Button Content="✕" Command="{Binding CloseCommand}" />
                    </StackPanel>
                </Border>
            </DataTemplate>
        </ItemsControl.ItemTemplate>
    </ItemsControl>
    
    <!-- TAB CONTENT -->
    <ContentControl Grid.Row="1" 
                    Content="{Binding ActiveTab.Content}" />
    
</Grid>

// Vorher:  14 Dialog-Fenster offen → Chaos
// Nachher: 1 Fenster mit Tabs → Organisiert ✓
```

---

### 8. 🟡 Theme Editor / Customization UI

#### Erklärung
**Problem:** Dark/Light Mode ist hart-codiert. User können Farben nicht anpassen.

**Lösung:** Theme-Editor UI, wo User Farben wählen können.

```csharp
// ✓ Theme Editor ViewModel
public class ThemeEditorViewModel : ObservableObject
{
    [ObservableProperty] private Color primaryColor = Colors.Blue;
    [ObservableProperty] private Color secondaryColor = Colors.Gray;
    
    [RelayCommand]
    public void ApplyTheme()
    {
        // Themes dynamisch aktualisieren
        App.Current.Styles[0] = GenerateThemeStyle(PrimaryColor, SecondaryColor);
    }
}

// ✓ XAML Theme Editor
<Window>
    <StackPanel>
        <TextBlock Text="Primary Color" />
        <ColorPicker Color="{Binding PrimaryColor}" />
        
        <TextBlock Text="Secondary Color" />
        <ColorPicker Color="{Binding SecondaryColor}" />
        
        <Button Content="Apply Theme" Command="{Binding ApplyThemeCommand}" />
    </StackPanel>
</Window>
```

---

### 9. 🟡 Advanced Search (Regex Support)

#### Erklärung
**Problem:** Search funktioniert nur mit Substring Match ("Lofi" findet "Lofi Beats").

**Lösung:** Regex Support für Power-Users: `/^Lofi.*beats$/i` findet Case-Insensitive Regex-Matches.

```csharp
// ✓ Advanced Search
public class AdvancedSearchService
{
    public bool MatchesQuery(string text, string query)
    {
        // Prüfe ob Regex
        if (query.StartsWith("/") && query.EndsWith("/"))
        {
            var regexPattern = query.Trim('/');
            return Regex.IsMatch(text, regexPattern, RegexOptions.IgnoreCase);
        }
        
        // Sonst normaler Substring
        return text.Contains(query, StringComparison.OrdinalIgnoreCase);
    }
}

// ✗ Vorher: Nur Substring
// Search: "Lofi"
// Findet: "Lofi Beats", "Beatlofi", "Lofi & Chill"

// ✓ Nachher: Mit Regex
// Search: "/^Lofi/"
// Findet: NUR "Lofi Beats", "Lofi Chill" (EXAKT am Anfang)
//
// Search: "/beats$/i"
// Findet: NUR Items, die mit "beats" ENDEN (Case-Insensitive)
```

---

## Zusammenfassung

| # | Task | Nutzen | Schwierigkeit |
|---|------|--------|-----------------|
| 1 | GetInstance() Pattern | Unit-Testing möglich | ⭐⭐ |
| 2 | Unit Tests | Sicherheit bei Änderungen | ⭐⭐⭐ |
| 3 | Thumbnail Cache | 95% schneller | ⭐ |
| 4 | Refactor ViewModels | Wartbarkeit +50% | ⭐⭐ |
| 5 | Pagination | Kostenlos 10x Performance | ⭐⭐ |
| 6 | Undo/Redo | User-Fehler-Toleranz | ⭐⭐ |
| 7 | MDI/Tabs | UI/UX Verbesserung | ⭐⭐⭐ |
| 8 | Theme Editor | Customization | ⭐ |
| 9 | Regex Search | Power-User Feature | ⭐⭐ |

**Empfehlung: Beginne mit Punkt 1-3 (1-2 Wochen), dann 4-5 (2 Wochen).**

