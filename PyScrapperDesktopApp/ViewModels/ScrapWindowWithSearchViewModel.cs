using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// ScrapWindowWithSearchViewModel is a view model class that manages the logic and data for a scrap window with search functionality in the PyScrapperDesktopApp.
/// It allows users to search for media content from various providers, select items from the search results, and initiate the scrap process to download the selected media.
/// The view model handles user interactions, communicates with the API client to perform search and scrap operations, and updates the user interface accordingly.
/// It also includes error handling and logging mechanisms to ensure a smooth user experience.
/// </summary>
public partial class ScrapWindowWithSearchViewModel : ObservableObject
{
    [ObservableProperty]
    private string _searchQuery;

    [ObservableProperty] 
    private int _searchResultsCount = 5;

    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _items = new();
    
    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _selectedItems = new();
    
    [ObservableProperty]
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes.Keys.ToList();
    
    [ObservableProperty]
    private string _selectedMediaType = "mp3";
    
    private readonly Window _scrapWindow;
    
    private readonly List<string> _providers = AppData.ValidSearchProviders;
    private readonly string _selectedProvider;
    
    public RelayCommand CancelCommand { get; set; }
    private DialogService _dialogService;

    private CancellationTokenSource? _cts;
    
    public event Action? RequestClose;
    
    private readonly AppLogger _logger = AppLogger.Instance;
    
    
    /// <summary>
    /// Constructor for the ScrapWindowWithSearchViewModel class, which initializes the view model with the provided scrap window and provider.
    /// It checks if the application is in design mode to avoid executing code that should only run at runtime, and it validates the provided provider against a list of supported providers. If the provider is valid, it sets up the CancelCommand to allow closing the window when requested.
    /// If any exceptions occur during initialization, it logs the error and displays a message box to inform the user before closing the window.
    /// </summary>
    /// <param name="scrapWindow"></param>
    /// <param name="provider"></param>
    /// <exception cref="Exception"></exception>
    public ScrapWindowWithSearchViewModel(Window scrapWindow, string provider, DialogService dialogService)
    {
        try
        {
            if (Design.IsDesignMode) return;

            _scrapWindow = scrapWindow;
            
            if (!_providers.Contains(provider)) throw new Exception("Provider not found");
                
            _selectedProvider = provider;

            CancelCommand = new RelayCommand(CancelDownload);
            
            _dialogService = dialogService;
        }
        catch (Exception ex)
        {
            var log = new Message($"Error initializing ScrapWindowWithSearchViewModel: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
                return;

            var messageBox = new MessageBox("An error occurred: " + ex.Message);
            messageBox.ShowDialog(desktop.MainWindow!);
            
            RequestClose?.Invoke();
        }
    }
    
    /// <summary>
    /// Scrap method that is executed when the user clicks the button to start the scrap process.
    /// It iterates through the selected items from the search results, prompts the user to enter a filename for each video, and sends a scrap request to the API for each item. If the scrap request is successful, it shows a progress window to track the download progress and updates the list of downloaded media in the AppData once the download is complete.
    /// If any errors occur during the scrap or download process, it displays a message box to inform the user and logs the error details.
    /// </summary>
    [RelayCommand]
    private async Task Scrap()
    {
        try
        {
            if (_cts is null)
            {
                _cts = new CancellationTokenSource();
            }
            else
            {
                _cts.Cancel();
                _cts.Dispose();
                _cts = new CancellationTokenSource();
            }

            var client = new ApiClient();

            List<string> Urls = new List<string>();
            List<string> FileNames = new List<string>();
            List<string> Paths = new List<string>();
            
            var topLevel = TopLevel.GetTopLevel(_scrapWindow);
            var storageService = new StorageService(topLevel!);
            var folder = await topLevel.StorageProvider.TryGetFolderFromPathAsync(AppData.Settings.DownloadPath!);

            foreach (var item in SelectedItems)
            {
                var options = new FilePickerSaveOptions()
                {
                    SuggestedStartLocation = folder,
                    SuggestedFileName = $"{item.title}{SelectedMediaType}",
                };

                var file = await storageService.SaveFilePickerAsync(options);

                if (file == null)
                {
                    
                    continue;
                }
                
                var filename = file.Name.Substring(0, file.Name.LastIndexOf('.'));
                var validFilename = DownloadedMedia.TryValidateFileName(filename, out var errorMessage);
                var downloadPath = file.Path.LocalPath;
                
                while (!validFilename)
                {
                    await _dialogService.ShowAlertAsync($"The filename \"{filename}\" is invalid: {errorMessage} Please rename the file and try again.");
                    
                    var log = new Message($"Invalid filename \"{filename}\" for item \"{item.identifier}\": {errorMessage}", DateTime.Now, "ERROR");
                    _logger.LogNewMassage(log);
                    
                    options = new FilePickerSaveOptions()
                    {
                        SuggestedStartLocation = folder,
                        SuggestedFileName = filename,
                    };
                    
                    file = await storageService.SaveFilePickerAsync(options);

                    if (file == null)
                    {
                        filename = null;
                        break;
                    }
                    
                    filename = file.Name.Substring(0, file.Name.LastIndexOf('.'));
                    validFilename = DownloadedMedia.TryValidateFileName(filename, out errorMessage);
                    downloadPath = file.Path.LocalPath;
                }

                Urls.Add(item.url);
                FileNames.Add(filename);
                Paths.Add(downloadPath);
            }

            DownloadRequestData requestData = new DownloadRequestData()
            {
                Provider = _selectedProvider,
                Urls = Urls,
                Filenames = FileNames,
                PreferredFile = SelectedMediaType.Trim('.'),
                PreferredType = AppData.ValidMediaTypes[SelectedMediaType],
                DownloadStrategy = "stream"
            };

            var result = await client.SendScrapRequest(requestData);

            int counter = 0;
            foreach (var resource in result.Resources)
            {
                if (result.TaskId != "-1")
                {
                    Task.Delay(2000).Wait();


                    var progressWindow = new ProgressBarWindow();
                    progressWindow.Show();

                    bool errorWhileDownloading = false;
                    if (progressWindow.DataContext is ProgressBarWindowViewModel vm)
                        errorWhileDownloading = await vm.StartProgress(resource);
                    
                    var ct =  new CancellationTokenSource();
                    
                    Task fileTask = new Task(async () => await client.GetFileFromStream(resource.DownloadUrl, Paths[counter], ct.Token));
                    
                    Thread fileThread = new Thread(fileTask.Start);
                    
                    fileThread.Start();
                    
                    if (!errorWhileDownloading)
                    {
                        Task.Delay(2000).Wait();

                        var downloadedFilePath =
                            Path.Combine(AppData.Settings.DownloadPath, $"{FileNames[counter]}{SelectedMediaType}");

                        bool isPlayable = false;

                        while (!isPlayable)
                        {
                            isPlayable = File.Exists(downloadedFilePath);
                        }

                        var req = new CreateDownloadedMediaRequest
                        {
                            UserIdentifier = AppData.CurrentUser.Identifier,
                            DownloadPath = downloadedFilePath,
                            DownloadedAt = DateTime.Now.ToString("o"),
                            MediaType = SelectedMediaType,
                            IsPlayable = isPlayable,
                            Title = FileNames[counter],
                            Url = Urls[counter]
                        };

                        var media = await Database.CreateDownloadedMediaAsync(req);

                        AppData.AddDownloadedMedia(media);
                    }
                    else
                    {
                        await _dialogService.ShowAlertAsync(
                            "An error occurred while downloading the media. Please try again.");
                    }
                }

                counter++;
            }

            _cts.Cancel();
            _cts.Dispose();
            RequestClose?.Invoke();
        }
        catch (OperationCanceledException)
        {
            CancelDownload();
        }
        catch (Exception ex)
        {
            var log = new Message($"An error occurred during the scrap process: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await _dialogService.ShowAlertAsync("An error occurred during the scrap process: " + ex.Message);
        }
    }

    /// <summary>
    /// Search method that is executed when the user clicks the button to perform a search based on the entered search query and selected provider.
    /// It sends a search request to the API with the specified search query, provider, and the number of top results to return.
    /// If the search is successful, it processes the search results and retrieves the thumbnail images for the results based on the provider.
    /// The search results are then displayed in the user interface for the user to select from.
    /// If no results are found, it shows a message box to inform the user and logs the search query with an appropriate message.
    /// If any errors occur during the search process, it displays a message box to inform the user and logs the error details.
    /// This functionality allows the user to easily search for media content from different providers and view relevant results directly within the scrap window.
    /// </summary>
    [RelayCommand]
    public async Task Search()
    {
        try
        {
            var client = new ApiClient();

            List<string> tags = ["track"];

            var filters = new SearchFilter()
            {
                Creator = "",
                Tags = tags
            };

            var requestData = new SearchRequestData()
            {
                Search = SearchQuery,
                Provider = _selectedProvider,
                Top = SearchResultsCount,
                Filters = filters
            };

            var results = await client.SendSearchRequest(requestData);

            var log = new Message("", DateTime.Now, "Init");

            if (results.Count == 0)
            {
                await _dialogService.ShowAlertAsync($"No results found for the given search query \"{SearchQuery}\".");

                log = new Message("No results found for query: " + SearchQuery, DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                return;
            }

            var httpClient = new HttpClient();

            var tasks = results.Select(async item =>
            {
                if (_selectedProvider == _providers[0])
                {
                    var thumbnailUrl = $"https://i.ytimg.com/vi/{item.identifier}/hqdefault.jpg";

                    var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);

                    var stream = new MemoryStream(bytes);
                    item.ThumbnailBitmap = new Bitmap(stream);
                }
                else 
                {
                    var thumbnailUrl = item.thumbnail;

                    var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);

                    var stream = new MemoryStream(bytes);
                    item.ThumbnailBitmap = new Bitmap(stream);
                }
            });

            await Task.WhenAll(tasks);

            httpClient.Dispose();

            Items = results;
        }
        catch (Exception ex)
        {
            var log = new Message($"An error occurred during the search process: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            await _dialogService.ShowAlertAsync("An error occurred during the search process: " + ex.Message);
        }
    }
    
    private void CancelDownload()
    {
        if (_cts == null)
            return;

        _cts.Cancel();
        _cts.Dispose();
        var log = new Message("Scrap operation was canceled by the user.", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        RequestClose?.Invoke();
    }
}