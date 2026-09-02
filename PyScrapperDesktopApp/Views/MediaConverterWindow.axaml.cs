using System.IO;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaConverterWindow : Window
{
    public MediaConverterWindow(string? path = null)
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new MediaConverterWindowViewModel(new DialogService(this), this);
        vm.CloseRequested += () => Close();
        DataContext = vm;

        if (!string.IsNullOrEmpty(path))
        {
            vm.FilePath = path;
            var filename = Path.GetFileName(path);
            vm.SelectButtonContent = $"Selected: {filename}";
            SelectButton.IsEnabled = false;
        }
    }
}