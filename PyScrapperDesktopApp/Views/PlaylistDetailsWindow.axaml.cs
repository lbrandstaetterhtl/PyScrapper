using System;
using System.Collections.Generic;
using System.IO;
using Avalonia.Controls;
using Avalonia.Interactivity;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class PlaylistDetailsWindow : Window
{
    public PlaylistDetailsWindow(Playlist playlist)
    {
        InitializeComponent();

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
                
                List<DownloadedMedia> mediaList = [media];

                var mediaPlayerWindow = new MediaPlayerWindow(mediaList);
                mediaPlayerWindow.Show();
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
}