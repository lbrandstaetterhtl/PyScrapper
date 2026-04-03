using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class ConfirmationWindow : Window
{
    public ConfirmationWindow(string message)
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new ConfirmationWindowViewModel(this, message);
        DataContext = vm;
    }
}