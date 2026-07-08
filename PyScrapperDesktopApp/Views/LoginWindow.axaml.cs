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
        
        DataContext = new LoginWindowViewModel(new DialogService(this), this);
    }
}