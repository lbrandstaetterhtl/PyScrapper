using Avalonia.Controls;
using Avalonia.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MainWindow : Window
{
    private MainWindowViewModel _vm;
    
    public MainWindow()
    {
        InitializeComponent();

        _vm = new MainWindowViewModel();
        
        DataContext = _vm;
        
        GetHealthItem.Click += async (sender, args) =>
        {
            await _vm.GetHealth();
            var messageBox = new MassageBox(_vm.HealthCheckResult);
            await messageBox.ShowDialog(this);
        };
    }
}