using Avalonia.Controls;
using Avalonia.Media;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class CreatePlaylistWindow : Window
{
    CreatePlaylistWindowViewModel _vm;
    public CreatePlaylistWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        DialogService ds = new DialogService(this);
        
        _vm = new CreatePlaylistWindowViewModel(ds);
        
        
        _vm.CloseRequested += Close;
        
        DataContext = _vm;
    }

    private void MediaTapped(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        if (sender is Border { DataContext: DownloadedMedia media } border)
        {
            if (border.IsTabStop)
            {
                border.IsTabStop = false;
                border.Opacity = 0.4;
                _vm.SelectedMedias.Add(media);
            }
            else
            {
                border.IsTabStop = true;
                border.Opacity = 1;
                _vm.SelectedMedias.Remove(media);
            }
        }
    }
}