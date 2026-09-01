using System;
using Avalonia.Controls;
using Avalonia.Controls.Chrome;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class LoginWindow : Window
{
    public LoginResult Result { get; set; } = LoginResult.Cancelled;

    public LoginWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new LoginWindowViewModel(new DialogService(this), this);
        DataContext = vm;
    }
    
    protected override void OnOpened(EventArgs e)
    {
        if (AppData.Config.LastLoggedInUser is null)
        {
            UsernameBox.Focus();
        }
        else
        {
            PasswordBox.Focus();
        }
    }
}