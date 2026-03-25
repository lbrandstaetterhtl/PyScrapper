using System;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaPlayerWindow : Window
{
    public MediaPlayerWindow(DownloadedMedia media = null, Playlist playlist = null)
    {
        InitializeComponent();
        
        var vm = new MediaPlayerWindowViewModel();
        DataContext = vm;

        VideoView.Initialized += OnVideoViewInitialized;
        Closing += OnWindowClosing;
        CloseButton.Click += (s, e) => Close();
        
        Opened += (_, _) =>
        {
            if (playlist != null)
                vm.LoadPlaylist(playlist);
            else
                vm._audioPlayer.PlayFile(media.DownloadPath);
        };
        
        VolumeSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is MediaPlayerWindowViewModel vm && VolumeSlider.IsFocused)
            {
                vm.Volume = (int)e.NewValue;
                vm._audioPlayer.MediaPlayer.Volume = vm.Volume;
            }
        };
    }
    
    private void OnVideoViewInitialized(object? sender, EventArgs e)
    {
        if (DataContext is MediaPlayerWindowViewModel vm)
        {
            VideoView.MediaPlayer = vm.MediaPlayer;
            
            vm.OnVideoViewReady(this);
            
            vm.VideoAvailableChanged += OnVideoAvailableChanged;
        }
    }
    
    private void OnVideoAvailableChanged(object? sender, bool hasVideo)
    {
        if (DataContext is MediaPlayerWindowViewModel vm)
        {
            VideoView.MediaPlayer = hasVideo ? vm.MediaPlayer : null;
        }
    }
    
    private void OnWindowClosing(object? sender, WindowClosingEventArgs e)
    {
        if (DataContext is MediaPlayerWindowViewModel vm)
        {
            vm.VideoAvailableChanged -= OnVideoAvailableChanged;
            vm.MediaPlayer.Stop();
        }
        
        VideoView.MediaPlayer = null;

        if (DataContext is IDisposable disposable)
        {
            disposable.Dispose();
        }
    }
}