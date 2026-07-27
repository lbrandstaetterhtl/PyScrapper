using System;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class LoginWindowViewModel(DialogService dialogService, LoginWindow window) : ObservableObject
{
    [ObservableProperty] 
    private string _username = "";

    [ObservableProperty] 
    private string _password = "";

    [RelayCommand]
    private async Task Login()
    {
        var client = new ApiClient(dialogService);
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await dialogService.ShowAlertAsync("Health check failed. Please check your connection or contact your admin.");
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

            window.Result = LoginResult.Success;
            window.Close();
        }
        else
        {
            var log = new Message("User login failed", DateTime.Now, "ERROR");
            var logger = new AppLogger();

            logger.LogNewMassage(log);

            await dialogService.ShowAlertAsync("Login failed. Please check your username and password.");
        }
    }

    [RelayCommand]
    private void Cancel()
    {
        window.Result = LoginResult.Cancelled;
        window.Close();
    }

    [RelayCommand]
    private async Task Register()
    {
        var client = new ApiClient(dialogService);
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await dialogService.ShowAlertAsync("Health check failed. Please check your connection or contact your admin.");
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
            await dialogService.ShowAlertAsync("Registration failed. Please check your username and password.");
        }
    }
}