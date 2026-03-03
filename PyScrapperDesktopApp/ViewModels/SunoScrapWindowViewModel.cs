using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Xml;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public class SunoScrapWindowViewModel : INotifyPropertyChanged
{
    private string _sunoUrl;
    
    private readonly List<string> _availableMediaType = [".mp3", ".mp4"];

    private string _selectedMediaTypes;
    
    private readonly Window _ScrapWindow;

    public string SunoUrl
    {
        get => _sunoUrl;
        set
        {
            _sunoUrl = value;
            OnPropertyChanged(nameof(SunoUrl));
        }
    }
    
    public string SelectedMediaType
    {
        get => _selectedMediaTypes;
        set
        {
            _selectedMediaTypes = value;
            OnPropertyChanged(nameof(SelectedMediaType));
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
    
    private async void Scrap()
    {
            ApiClient client = new();
        
            string serverUrl = "127.0.0.1:8765";
        
            var requestData = new ApiClient.RequestData
            {
                Provider = "suno",
                Url = SunoUrl,
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

    public SunoScrapWindowViewModel(Window scrapWindow)
    {
        _ScrapWindow = scrapWindow;
    
        ScrapCommand = new RelayCommand(Scrap);
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
}