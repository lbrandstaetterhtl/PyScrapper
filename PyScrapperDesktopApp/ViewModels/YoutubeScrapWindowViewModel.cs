using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class YoutubeScrapWindowViewModel : INotifyPropertyChanged
{
    private string _searchQuery;

    private string _searchResultsCount;

    private List<ApiClient.YoutubeVideoItem> _youtubeVideoItems = new();
    
    private List<ApiClient.YoutubeVideoItem> _selectedYoutubeVideoItem = new();
    
    private readonly List<string> _availableMediaType = [".mp3", ".mp4"];
    
    private readonly Window _ScrapWindow;

    public List<ApiClient.YoutubeVideoItem> YoutubeVideoItems
    {
        get => _youtubeVideoItems;
        set
        {
            if (_youtubeVideoItems != value)
            {
                _youtubeVideoItems = value;
                OnPropertyChanged(nameof(YoutubeVideoItems));
            }
        }
    }

    public List<ApiClient.YoutubeVideoItem> SelectedYoutubeVideoItems
    {
        get => _selectedYoutubeVideoItem;
        set
        {
            if (_selectedYoutubeVideoItem != value)
            {
                _selectedYoutubeVideoItem = value;
                OnPropertyChanged(nameof(SelectedYoutubeVideoItems));
            }
        }
    }
    
    public string SearchResultsCount
    {
        get => _searchResultsCount;
        set
        {
            if (_searchResultsCount != value)
            {
                _searchResultsCount = value;
                OnPropertyChanged(nameof(SearchResultsCount));
            }
        }
    }
    
    public string SearchQuery
    {
        get => _searchQuery;
        set
        {
            if (_searchQuery != value)
            {
                _searchQuery = value;
                OnPropertyChanged(nameof(SearchQuery));
            }
        }
    }
    
    private string _selectedMediaType;
    
    public string SelectedMediaType
    {
        get => _selectedMediaType;
        set
        {
            if (_selectedMediaType != value)
            {
                _selectedMediaType = value;
                OnPropertyChanged(nameof(SelectedMediaType));
            }
        }
    }
    
    public RelayCommand CancelCommand { get; set; }
    
    public IEnumerable<string> AvailableMediaTypes => _availableMediaType;
    
    public event PropertyChangedEventHandler? PropertyChanged;
    
    private void OnPropertyChanged(string propertyName)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
    
    public event Action? RequestClose;
    
    public YoutubeScrapWindowViewModel(Window ScrapWindow)
    {
        _ScrapWindow = ScrapWindow;
        
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
    
    [RelayCommand]
    public async void Scrap()
    {
        var client = new ApiClient();
        
        string serverUrl = "127.0.0.1:8765";

        var requestData = new ApiClient.DownloadRequestData();

        foreach (var item in SelectedYoutubeVideoItems)
        {
            requestData = new ApiClient.DownloadRequestData()
            {
                Provider = "youtube",
                Url = item.url,
                Mediatype = SelectedMediaType,
                Download_path = AppData.DownloadPath
            };
            
            var result = await client.SendScrapRequest(requestData, serverUrl);
        
            if (!result)
            {
                var massageBox = new MassageBox($"Failed to start scraping. Please check the server/app logs for more details.");
                await massageBox.ShowDialog(_ScrapWindow);
                return;
            }
        }
        
        RequestClose?.Invoke();
    }

    [RelayCommand]
    public async void Search()
    {
        var client = new ApiClient();

        string serverUrl = "127.0.0.1:8765";

        var requestData = new ApiClient.SearchRequestData()
        {
            Search = SearchQuery,
            Provider = "youtube",
            Top = Convert.ToInt32(SearchResultsCount),
        };
        
        var results = await client.SendSearchRequest(requestData, serverUrl);
        
        if (results.Count == 0)
        {
            var massageBox = new MassageBox($"No results found for query: {SearchQuery}. Please try a different query.");
            await massageBox.ShowDialog(_ScrapWindow);
            return;
        }
        
        foreach (var item in results)
        {
            using var httpClient = new HttpClient();
            var bytes = await httpClient.GetByteArrayAsync(item.thumbnail);
            using var stream = new MemoryStream(bytes);
            item.ThumbnailBitmap = new Bitmap(stream);
        }
        
        YoutubeVideoItems = results;
    }
}