using System;
using System.Collections.Generic;
using System.ComponentModel;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public class YoutubeScrapWindowViewModel : INotifyPropertyChanged
{
    private string _youtubeUrl;
    
    private readonly List<string> _availableMediaType = [".mp3", ".mp4"];
    
    private readonly Window _ScrapWindow;
    
    public string YoutubeUrl
    {
        get => _youtubeUrl;
        set
        {
            if (_youtubeUrl != value)
            {
                _youtubeUrl = value;
                OnPropertyChanged(nameof(YoutubeUrl));
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
    
    public RelayCommand ScrapCommand { get; set; }
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
        
        ScrapCommand = new RelayCommand(Scrap);
    }
    
    private async void Scrap()
    {
        var client = new ApiClient();
        
        string serverUrl = "127.0.0.1:8765";
        
        var requestData = new ApiClient.RequestData
        {
            Provider = "youtube",
            Url = YoutubeUrl,
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
        
        RequestClose?.Invoke();
    }
}