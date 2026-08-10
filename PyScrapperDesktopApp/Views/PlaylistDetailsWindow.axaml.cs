using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Interactivity;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class PlaylistDetailsWindow : Window
{
    private readonly Window _mainWindow;
    private readonly AppLogger _logger = AppLogger.Instance;

    public PlaylistDetailsWindow(string identifier)
    {
        InitializeComponent();
        TitleBar.Initialize(this);

        _mainWindow = App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null;
        
        DialogService ds = new DialogService(this);

        var vm = new PlaylistDetailsWindowViewModel(identifier, ds);

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

                //TODO: Need new Mediaplayer logic
            }
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

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

    public async void RemoveButtonClick(object? sender, RoutedEventArgs e)
    {
        try
        {

            if (sender is MenuItem { DataContext: DownloadedMedia media })
            {
                if (DataContext is PlaylistDetailsWindowViewModel vm)
                {
                    await Database.DeletePlaylistMediaAsync(media.Identifier, vm._playlist.Identifier);
                    vm._playlist.RemoveMedia(media.Identifier);
                    vm.RefreshMedias();
                }
            }
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while trying to remove the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            var messageBox = new MessageBox("An error occurred while trying to remove the media: " + ex.Message);
            _ = messageBox.ShowDialog(this);
        }
    }
}