using System;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class LoginWindowViewModel : ObservableObject
{
    [ObservableProperty] 
    private string _username = "";

    [ObservableProperty] 
    private string _password = "";
    
    private readonly AppLogger _logger = AppLogger.Instance;
    private readonly DialogService _dialogService;
    private readonly LoginWindow _window;

    public LoginWindowViewModel(DialogService dialogService, LoginWindow window)
    {
        _dialogService = dialogService;
        _window = window;

        if (AppData.Config.LastLoggedInUser is not null)
        {
            Username = AppData.Config.LastLoggedInUser.Username;
        }
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Login" button.
    /// It performs a health check on the API client, sends a login request with the provided username and password, and handles the response.
    /// If the login is successful, it logs the event, sets the result of the login window to success, and closes the window.
    /// If the login fails, it logs the event and displays an alert dialog to inform the user of the failure.
    /// </summary>
    [RelayCommand]
    private async Task Login()
    {
        var client = new ApiClient();
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await _dialogService.ShowAlertAsync("Health check failed. Please check your connection.");
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

            _logger.LogNewMassage(log);

            _window.Result = LoginResult.Success;
            _window.Close();
        }
        else
        {
            var log = new Message("User login failed", DateTime.Now, "ERROR");

            _logger.LogNewMassage(log);

            await _dialogService.ShowAlertAsync("Login failed. Please check your username and password.");
        }
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Cancel" button.
    /// It sets the result of the login window to cancelled and closes the window.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        _window.Result = LoginResult.Cancelled;
        _window.Close();
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Register" button.
    /// It performs a health check on the API client, sends a registration request with the provided username and password, and handles the response.
    /// If the registration is successful, it automatically calls the Login method to log in the user.
    /// If the registration fails, it displays an alert dialog to inform the user of the failure.
    /// </summary>
    [RelayCommand]
    private async Task Register()
    {
        var client = new ApiClient();
        
        var healthResponse = await client.GetHealth();

        if (!healthResponse.Ok)
        {
            await _dialogService.ShowAlertAsync("Health check failed. Please check your connection.");
            return;
        }

        var req = new RegisterRequest()
        {
            Username = Username,
            Password = Password,
            ApiKey = SecretProtector.GenerateApiKey()
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