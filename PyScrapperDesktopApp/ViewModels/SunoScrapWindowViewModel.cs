using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Xml;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public class SunoScrapWindowViewModel : INotifyPropertyChanged
{
    private string _sunoUrl;
    
    private readonly List<string> _availableMediaType = [".mp3", ".mp4"];

    private string _selectedMediaTypes;

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
        HttpClient client = new();
        const string serverUrl = "127.0.0.1:8765";
        
        if (SelectedMediaType != ".mp3" && SelectedMediaType != ".mp4")
        {
            throw new InvalidOperationException("Invalid media type selected.");
        }

        var requestData = new
        {
            provider = "suno",
            url = SunoUrl,
            mediatype = SelectedMediaType,
        };
        
        await client.PostAsJsonAsync($"http://{serverUrl}/download", requestData);
        
        RequestClose?.Invoke();
    }

    public SunoScrapWindowViewModel()
    {
        ScrapCommand = new RelayCommand(Scrap);
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
}