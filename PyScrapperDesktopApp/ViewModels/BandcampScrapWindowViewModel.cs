using System;
using System.Collections.Generic;
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

public partial class BandcampScrapWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _searchQuery;

    [ObservableProperty]
    private string _searchResultsCount;

    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _items = new();
    
    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _selectedItems = new();
    
    [ObservableProperty]
    private Window _ScrapWindow;
    
    public RelayCommand CancelCommand { get; set; }
    
    public event Action? RequestClose;
    
    public BandcampScrapWindowViewModel(Window scrapWindow)
    {
        if (Design.IsDesignMode) return;
        
        _ScrapWindow = scrapWindow;
        
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }

    [RelayCommand]
    private async Task Scrap()
    {
        var client = new ApiClient();

        string serverUrl = "127.0.0.1:8765";

        var requestData = new DownloadRequestData();

        foreach (var item in SelectedItems)
        {
            var inputWindow = new InputWindow($"Enter filename for the video '{item.title}' (without extension):");
            var filename = await inputWindow.ShowDialog<string>(ScrapWindow);
            
            requestData = new DownloadRequestData()
            {
                Provider = "bandcamp",
                Url = item.url,
                Mediatype = ".mp3",
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
                    var identifier = "bandcamp_" + item.title;
                    
                    var downloadedFilePath = Path.Combine(AppData.DownloadPath, $"{filename}.mp3");
                    
                    var isPlayable = File.Exists(downloadedFilePath);
                    
                    var media = new DownloadedMedia(item.url, ".mp3", DateTime.Now, downloadedFilePath, isPlayable, identifier);
                    
                    media.SetHighestId(AppData.DownloadedMedias);
                    
                    AppData.AddDownloadedMedia(media);
                }
                else
                {
                    var messageBox = new MessageBox("Error while downloading the media. Please check the logs for more details.");
                    await messageBox.ShowDialog(_ScrapWindow);
                }
                
                Task.Delay(2000).Wait();
            }
        }
        
        RequestClose?.Invoke();
    }

    [RelayCommand]
    public async Task Search()
    {
        var client = new ApiClient();

        string serverUrl = "127.0.0.1:8765";
        
        var searchRequestData = new SearchRequestData()
        {
            Provider =  "bandcamp",
            Search = SearchQuery,
            Top = Convert.ToInt32(SearchResultsCount)
        };

        var searchResults = await client.SendSearchRequest(searchRequestData, serverUrl);

        foreach (var searchResult in searchResults)
        {
            using var httpClient = new HttpClient();
            var thumbnailUrl = searchResult.thumbnail;
            
            var bytes = await httpClient.GetByteArrayAsync(thumbnailUrl);
            
            using var stream = new MemoryStream(bytes);

            searchResult.ThumbnailBitmap = new Bitmap(stream);
        }
        
        Items = searchResults;
    }
}