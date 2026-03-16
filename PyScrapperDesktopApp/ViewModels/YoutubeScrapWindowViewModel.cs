using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class YoutubeScrapWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _searchQuery;

    [ObservableProperty]
    private string _searchResultsCount;

    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _youtubeVideoItems = new();
    
    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _selectedYoutubeVideoItems = new();
    
    [ObservableProperty]
    private List<string> _availableMediaTypes = [".mp3", ".mp4"];
    
    [ObservableProperty]
    private string _selectedMediaType;
    
    [ObservableProperty]
    private Window _ScrapWindow;
    
    
    public RelayCommand CancelCommand { get; set; }
    
    public event Action? RequestClose;
    
    public YoutubeScrapWindowViewModel(Window scrapWindow)
    {
        if (Design.IsDesignMode) return;
        
        _ScrapWindow = scrapWindow;
        
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
    
    [RelayCommand]
    public async Task Scrap()
    {
        var client = new ApiClient();
        
        string serverUrl = "127.0.0.1:8765";

        var requestData = new DownloadRequestData();

        foreach (var item in SelectedYoutubeVideoItems)
        {
            var inputWindow = new InputWindow($"Enter filename for the video '{item.title}' (without extension):");
            var filename = await inputWindow.ShowDialog<string>(_ScrapWindow);
            
            requestData = new DownloadRequestData()
            {
                Provider = "youtube",
                Url = item.url,
                Mediatype = SelectedMediaType,
                Filename = filename,
                Download_path = AppData.DownloadPath
            };
            
            var result = await client.SendScrapRequest(requestData, serverUrl);
        
            if (result != "-1")
            { 
                Task.Delay(2000).Wait();
                 
                var progressWindow = new ProgressBarWindow();
                progressWindow.Show();
                
                bool errorWhileDownloading = false;
                if (progressWindow.DataContext is ProgressBarWindowViewModel vm)
                    errorWhileDownloading = await vm.StartProgress(result);

                if (!errorWhileDownloading)
                {
                    var identifier = item.url.Split('=')[^1];

                    var downloadFilePath = Path.Combine(AppData.DownloadPath, $"{filename}{SelectedMediaType}");

                    bool isPlayable = File.Exists(downloadFilePath);

                    var media = new DownloadedMedia(item.url, SelectedMediaType, DateTime.Now, downloadFilePath,
                        isPlayable, identifier);
                    media.SetHighestId(AppData.DownloadedMedias);

                    AppData.AddDownloadedMedia(media);
                }
                else
                {
                    var massageBox = new MessageBox("Download failed, check logs for more details");
                    await massageBox.ShowDialog(_ScrapWindow);
                }
                
                Task.Delay(1000).Wait();
            }
        }
        
        RequestClose?.Invoke();
    }

    [RelayCommand]
    public async Task Search()
    {
        var client = new ApiClient();

        string serverUrl = "127.0.0.1:8765";

        var requestData = new SearchRequestData()
        {
            Search = SearchQuery,
            Provider = "youtube",
            Top = Convert.ToInt32(SearchResultsCount),
        };
        
        var results = await client.SendSearchRequest(requestData, serverUrl);

        var log = new Massage("", DateTime.Now, "Init");
        
        if (results.Count == 0)
        {
            var massageBox = new MessageBox($"No results found for query: {SearchQuery}. Please try a different query.");
            await massageBox.ShowDialog(_ScrapWindow);
            
            log = new Massage("No results found for query: " + SearchQuery, DateTime.Now, "INFO");
            new AppLogger().LogNewMassage(log);
            
            return;
        }
        
        foreach (var item in results)
        {
            using var httpClient = new HttpClient();
            var thumbnailUrl = $"https://i.ytimg.com/vi/{item.identifier}/hqdefault.jpg";

            var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);
            
            using var stream = new MemoryStream(bytes);
            item.ThumbnailBitmap = new Bitmap(stream);
        }
        
        YoutubeVideoItems = results;
    }
}