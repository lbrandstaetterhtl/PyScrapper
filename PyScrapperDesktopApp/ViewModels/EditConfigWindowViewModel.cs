using System;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class EditConfigWindowViewModel : ObservableObject
{
    [ObservableProperty] private string _serverUrl;
    [ObservableProperty] private string _serverPort;
    [ObservableProperty] private string _myApiKey;
    
    private readonly DialogService _dialogService;
    
    public Action CloseRequested { get; set; }
    
    public EditConfigWindowViewModel(AppConfig config, DialogService dialogService)
    {
        _serverUrl = config.ServerUrl;
        _serverPort = config.ServerPort;
        _myApiKey = SecretProtector.Decrypt(AppData.CurrentUser.ApiKey) ?? "Not found";
        _dialogService = dialogService;
    }
    
    [RelayCommand]
    private async Task Save()
    {
        var config = new AppConfig
        {
            ServerUrl = ServerUrl,
            ServerPort = ServerPort,
            LastLoggedInUser = AppData.Config.LastLoggedInUser
        };
        
        AppData.Config = config;
        AppConfig.Save(config);


        if (!MyApiKey.Equals("Not found"))
        {
            if (!AppData.CurrentUser.ApiKey.Equals(MyApiKey))
            {
                var confirmed = await _dialogService.ConfirmAsync(
                    "API Key has changed. You may not be able to use this app properly. Do you want to continue?");
                
                if (confirmed)
                {
                    AppData.CurrentUser.ApiKey = SecretProtector.Encrypt(MyApiKey);
                }
            }
        }
    }

    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}