using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class CreatePlaylistWindow : Window
{
    public CreatePlaylistWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        DialogService ds = new DialogService(this);
        
        var vm = new CreatePlaylistWindowViewModel(ds);
        
        DataContext = vm;
        
        vm.CloseRequested += Close;
    }
}