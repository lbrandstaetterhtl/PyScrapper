using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaConverterWindow : Window
{
    public MediaConverterWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new MediaConverterWindowViewModel(new DialogService(this), this);
        vm.CloseRequested += () => Close();
        DataContext = vm;
    }
}