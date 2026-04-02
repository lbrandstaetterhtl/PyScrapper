using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Media.Imaging;
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
    private List<string> _availableMediaTypes = [".mp3", ".mp4"];
    
    [ObservableProperty]
    private string _selectedMediaType = ".mp3";
    
    private readonly Window _scrapWindow;
    
    private readonly List<string> _providers = ["youtube", "suno", "bandcamp", "youtube.com", "suno.com", "bandcamp.com"];
    private readonly string _selectedProvider;
    
    public RelayCommand CancelCommand { get; set; }
    
    public event Action? RequestClose;
    
    /// <summary>
    /// Constructor for the ScrapWindowWithSearchViewModel class, which initializes the view model with the provided scrap window and provider.
    /// It checks if the application is in design mode to avoid executing code that should only run at runtime, and it validates the provided provider against a list of supported providers. If the provider is valid, it sets up the CancelCommand to allow closing the window when requested.
    /// If any exceptions occur during initialization, it logs the error and displays a message box to inform the user before closing the window.
    /// </summary>
    /// <param name="scrapWindow"></param>
    /// <param name="provider"></param>
    /// <exception cref="Exception"></exception>
    public ScrapWindowWithSearchViewModel(Window scrapWindow, string provider)
    {
        try
        {
            if (Design.IsDesignMode) return;

            _scrapWindow = scrapWindow;
            
            if (!_providers.Contains(provider)) throw new Exception("Provider not found");
                
            _selectedProvider = provider;

            CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
        }
        catch (Exception ex)
        {
            var log = new Massage($"Error initializing ScrapWindowWithSearchViewModel: {ex.Message}", DateTime.Now, "ERROR");
            new AppLogger().LogNewMassage(log);

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
        var client = new ApiClient();

        foreach (var item in SelectedItems)
        {
            string filename;
            
            while (true)
            {
                var inputWindow = new InputWindow($"Enter filename for the media '{item.title}' (without extension):");
                filename = await inputWindow.ShowDialog<string>(_scrapWindow);

                if (filename == null)
                {
                    return;
                }

                filename = filename.Trim();

                if (TryValidateFileName(filename, out var error))
                {
                    break;
                }

                var messageBox = new MessageBox(error);
                await messageBox.ShowDialog(_scrapWindow);
            }

            var requestData = new DownloadRequestData()
            {
                Provider = _selectedProvider,
                Url = item.url,
                Mediatype = SelectedMediaType,
                Filename = filename,
                Download_path = AppData.Settings.DownloadPath!
            };
            
            var result = await client.SendScrapRequest(requestData);
        
            if (result != "-1")
            { 
                Task.Delay(2000).Wait();
                 
                var progressWindow = new ProgressBarWindow();
                progressWindow.Show();

                var vm = progressWindow.DataContext as ProgressBarWindowViewModel;

                if (vm == null)
                {
                    var messageBox = new MessageBox("ProgressBar ViewModel not found");
                    await messageBox.ShowDialog(_scrapWindow);
                    continue;
                }

                bool errorWhileDownloading = await vm.StartProgress(result);
                
                if (!errorWhileDownloading)
                {
                    await vm.WaitUntilFinished();
                    
                    var identifier = item.url.Split('=')[^1];

                    var downloadFilePath = Path.Combine(AppData.Settings.DownloadPath!, $"{filename}{SelectedMediaType}");

                    Task.Delay(2000).Wait();
                    
                    bool isPlayable = File.Exists(downloadFilePath);

                    var media = new DownloadedMedia(item.url, SelectedMediaType, DateTime.Now, downloadFilePath,
                        isPlayable, identifier);
                    media.SetHighestId(AppData.DownloadedMedias);
                    media.SetTitle();

                    AppData.AddDownloadedMedia(media);
                }
                else
                {
                    var massageBox = new MessageBox("Download failed, check logs for more details");
                    await massageBox.ShowDialog(_scrapWindow);
                }
                
                Task.Delay(1000).Wait();
            }
        }
        
        RequestClose?.Invoke();
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
        var client = new ApiClient();

        var requestData = new SearchRequestData()
        {
            Search = SearchQuery,
            Provider = _selectedProvider,
            Top = SearchResultsCount,
        };
        
        var results = await client.SendSearchRequest(requestData);

        var log = new Massage("", DateTime.Now, "Init");
        
        if (results.Count == 0)
        {
            var massageBox = new MessageBox($"No results found for query: {SearchQuery}. Please try a different query.");
            await massageBox.ShowDialog(_scrapWindow);
            
            log = new Massage("No results found for query: " + SearchQuery, DateTime.Now, "INFO");
            new AppLogger().LogNewMassage(log);
            
            return;
        }

        var httpClient = new HttpClient();
        
        if (_selectedProvider == _providers[0] || _selectedProvider == _providers[3])
        {
            foreach (var item in results)
            {
                var thumbnailUrl = $"https://i.ytimg.com/vi/{item.identifier}/hqdefault.jpg";

                var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);

                using var stream = new MemoryStream(bytes);
                item.ThumbnailBitmap = new Bitmap(stream);
            }
        }
        else if (_selectedProvider == _providers[2] || _selectedProvider == _providers[5])
        {
            foreach (var item in results)
            {
                var thumbnailUrl = item.thumbnail;

                var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);

                using var stream = new MemoryStream(bytes);
                item.ThumbnailBitmap = new Bitmap(stream);
            }
        }
        
        httpClient.Dispose();

        Items = results;
    }
    
    private static readonly HashSet<string> ReservedWindowsNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    };

    /// <summary>
    /// Tries to validate the provided file name by checking if it is not empty, does not end with a space or dot, does not contain invalid characters, and is not a reserved Windows name.
    /// If the file name is valid, it returns true; otherwise, it returns false and provides an appropriate error message indicating the reason for the validation failure.
    /// </summary>
    /// <param name="fileName"></param>
    /// <param name="errorMessage"></param>
    /// <returns></returns>
    private static bool TryValidateFileName(string? fileName, out string errorMessage)
    {
        errorMessage = string.Empty;

        if (string.IsNullOrWhiteSpace(fileName))
        {
            errorMessage = "Filename must not be empty.";
            return false;
        }

        fileName = fileName.Trim();

        if (fileName.EndsWith(' ') || fileName.EndsWith('.'))
        {
            errorMessage = "Filename must not end with a space or dot.";
            return false;
        }

        if (fileName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
        {
            errorMessage = "Filename contains invalid characters.";
            return false;
        }

        if (ReservedWindowsNames.Contains(fileName))
        {
            errorMessage = "Filename is a reserved Windows name.";
            return false;
        }

        return true;
    }
}