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
    }
}