using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class CreatePlaylistWindow : Window
{
    public CreatePlaylistWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new CreatePlaylistWindowViewModel(this);
        
        DataContext = vm;
        
        vm.CloseRequested += Close;
    }
}