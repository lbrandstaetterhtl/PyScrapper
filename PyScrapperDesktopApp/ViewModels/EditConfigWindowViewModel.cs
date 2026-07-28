using System;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class EditConfigWindowViewModel : ObservableObject
{
    [ObservableProperty] private string _serverUrl;
    [ObservableProperty] private string _serverPort;
    [ObservableProperty] private string _apiKey;
    
    private readonly DialogService _dialogService;
    
    public Action CloseRequested { get; set; }
    
    public EditConfigWindowViewModel(AppConfig config, DialogService dialogService)
    {
        _serverUrl = config.ServerUrl;
        _serverPort = config.ServerPort;
        _apiKey = config.ApiKey;
        _dialogService = dialogService;
    }
    
    [RelayCommand]
    private void Save()
    {
        var config = new AppConfig
        {
            ServerUrl = _serverUrl,
            ServerPort = _serverPort,
            ApiKey = _apiKey
        };
        
        AppData.Config = config;
        AppConfig.Save(config);
    }

    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}