using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
    private PlaylistDetailsWindowViewModel _vm;

    public PlaylistDetailsWindow(string identifier)
    {
        InitializeComponent();
        TitleBar.Initialize(this);

        _mainWindow = App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null;

        var vm = new PlaylistDetailsWindowViewModel(identifier);

        DataContext = vm;

        vm.CloseRequested += Close;
        _vm = vm;
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

                if (_mainWindow is MainWindow mainWindow)
                {
                    var tmpPlaylist = new Playlist(media.Title, "", "12345", AppData.CurrentUser.Identifier);
                    tmpPlaylist.MediaIdentifiers.Add(media.Identifier);
                    mainWindow.MediaPlayer.LoadAndPlay(tmpPlaylist);
                }
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
                    var req = new DeletePlaylistMediaRequest()
                    {
                        PlaylistIdentifier = _vm.PlaylistId,
                        MediaIdentifier = media.Identifier
                    };
                    await Database.DeletePlaylistMediaAsync(req);
                    vm._playlist.RemoveMedia(media.Identifier);
                    await vm.RefreshMedias();
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

    public void AddMediaClick(object? sender, RoutedEventArgs e)
    {
        MediasInPlaylist.IsVisible = false;
        Search.IsVisible = true;
        SearchedMedias.IsVisible = true;
        AddButton.IsVisible = false;
    }

    public async void DoubleClickSearchedMedia(object? sender, RoutedEventArgs e)
    {
        if (sender is Border { DataContext: DownloadedMedia media })
        {
           await _vm._playlist.AddNewMedia(media.Identifier);
           await _vm.RefreshMedias();
        }
        
        Search.IsVisible = false;
        MediasInPlaylist.IsVisible = true;
        SearchedMedias.IsVisible = false;
    }

    public void CloseSearchClick(object? sender, RoutedEventArgs e)
    {
        Search.IsVisible = false;
        MediasInPlaylist.IsVisible = true;
        SearchedMedias.IsVisible = false;
        AddButton.IsVisible = true;
    }
}