using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Net.Http.Json;
using System.Xml;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public class SunoScrapWindowViewModel : INotifyPropertyChanged
{
    private readonly AppLogger _logger = new();
    
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
        try
        {
            ApiClient client = new();
        
            string serverUrl = "127.0.0.1:8765"; // Replace with your actual server URL
        
            var requestData = new RequestData
            {
                Provider = "suno",
                Url = SunoUrl,
                MediaType = SelectedMediaType
            };
        
            await client.SendScrapRequest(requestData, serverUrl);
        
            RequestClose?.Invoke();
        }
        catch (Exception e)
        {
            var massage = new Massage($"Error during scraping: {e.Message}", DateTime.Now, "ERROR");
            
            _logger.LogNewMassage(massage);
        }
    }

    public SunoScrapWindowViewModel()
    {
        ScrapCommand = new RelayCommand(Scrap);
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
}