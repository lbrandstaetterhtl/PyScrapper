using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();

        var vm = new MainWindowViewModel();
        
        DataContext = vm;
        
        GetHealthItem.Click += async (sender, args) =>
        {
            await vm.GetHealth();
            var messageBox = new MassageBox(vm.HealthCheckResult);
            await messageBox.ShowDialog(this);
        };
    }
}