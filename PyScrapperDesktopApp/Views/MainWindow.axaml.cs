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
        
        Suno.Click += (sender, args) =>
        {
            vm.ScrapSuno("https://suno.com/song/52d38334-5459-409f-b935-e3f35d99e112", ".mp3");
        };
    }
}