using System;
using System.Threading.Tasks;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class LoginWindowViewModel : ObservableObject
{
    [ObservableProperty]
    public string _username;

    [ObservableProperty]
    public string _password;

    private readonly DialogService _dialogService;
    private readonly LoginWindow _window;

    public LoginWindowViewModel(DialogService dialogService, LoginWindow window)
    {
        _dialogService = dialogService;
        _window = window;
    }

    [RelayCommand]
    public async Task Login()
    {
        var client = new ApiClient(_dialogService);
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await _dialogService.ShowAlertAsync("Health check failed. Please check your connection or contact your admin.");
            return;
        }

        var req = new LoginRequest()
        {
            Username = Username,
            Password = Password
        };

        var response = await client.Login(req);

        if (response)
        {
            var log = new Message("User logged in successfully", DateTime.Now, "INFO");
            var logger = new AppLogger();

            logger.LogNewMassage(log);

            _window.Result = LoginResult.Success;
            _window.Close();
        }
        else
        {
            var log = new Message("User login failed", DateTime.Now, "ERROR");
            var logger = new AppLogger();

            logger.LogNewMassage(log);

            await _dialogService.ShowAlertAsync("Login failed. Please check your username and password.");
        }
    }

    [RelayCommand]
    public void Cancel()
    {
        _window.Result = LoginResult.Cancelled;
        _window.Close();
    }

    [RelayCommand]
    private async Task Register()
    {
        var client = new ApiClient(_dialogService);
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await _dialogService.ShowAlertAsync("Health check failed. Please check your connection or contact your admin.");
            return;
        }

        var req = new RegisterRequest()
        {
            Username = Username,
            Password = Password
        };

        var result = await client.Register(req);

        if (result)
        {
            await Login();
        }
        else
        {
            await _dialogService.ShowAlertAsync("Registration failed. Please check your username and password.");
        }
    }
}