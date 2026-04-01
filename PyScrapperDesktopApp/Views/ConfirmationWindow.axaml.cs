using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class ConfirmationWindow : Window
{
    public ConfirmationWindow(string message)
    {
        InitializeComponent();
        
        var vm = new ConfirmationWindowViewModel(this, message);
        DataContext = vm;
    }
}