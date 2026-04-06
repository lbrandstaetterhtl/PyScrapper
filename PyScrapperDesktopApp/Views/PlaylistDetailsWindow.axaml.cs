using System;
using System.Collections.Generic;
using System.IO;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Interactivity;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class PlaylistDetailsWindow : Window
{
    private readonly Window _mainWindow;
    
    public PlaylistDetailsWindow(Playlist playlist)
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        _mainWindow = App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null;

        var vm = new PlaylistDetailsWindowViewModel(playlist);
        
        DataContext = vm;
        
        vm.CloseRequested += Close;
    }
    
    private void PlayMedia(DownloadedMedia media)
    {
        try
        {
            if (media.IsPlayable)
            {
                if (!File.Exists(media.DownloadPath))
                {
                    media.IsPlayable = false;
                    throw new Exception("Media not found");
                }
                
                List<int> mediaIds = [media.Id];
                Playlist playlist = new Playlist(mediaIds, "NPLL", "");

                if (_mainWindow is MainWindow mainWindow)
                {
                    mainWindow.MediaPlayer.LoadAndPlay(playlist);
                }
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            var logger = new AppLogger();
            logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while trying to play the media: " + ex.Message);
            _ = messageBox.ShowDialog(this);
        }
    }
    
    public void DoubleClickMedia(object? sender, RoutedEventArgs e)
    {
        if (sender is Border { DataContext: DownloadedMedia media })
        {
            PlayMedia(media);
        }
    }
    
    public void PlayButtonClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            PlayMedia(media);
        }
    }
    
    public void RemoveButtonClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            if (DataContext is PlaylistDetailsWindowViewModel vm)
            {
                vm._playlist.RemoveMedia(media.Id);
                vm.RefreshMedias();
            }
        }
    }
}