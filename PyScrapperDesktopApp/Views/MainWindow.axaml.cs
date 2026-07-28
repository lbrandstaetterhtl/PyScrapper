using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Threading;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MainWindow : Window
{
    private MainWindowViewModel _vm;
    private readonly AppLogger _logger = AppLogger.Instance;
    
    private DialogService _ds;

    public MainWindow()
    {
        if (Design.IsDesignMode) return;

        InitializeComponent();
        TitleBar.Initialize(this);

        _ds = new DialogService(this);
        
        _vm = new MainWindowViewModel(_ds);
        DataContext = _vm;

        Opened += (s, e) =>
        {
            _vm.OnWindowReady(this);

            MediaPlayer.OnCompactChanged += (isCompact) =>
            {
                var outerGrid = (Grid)((Grid)Content).Children[1];
                if (isCompact)
                {
                    outerGrid.RowDefinitions[2].Height = GridLength.Auto;
                    _vm.MediaPlayerMinHeight = 65;
                }
                else
                {
                    outerGrid.RowDefinitions[2].Height = new GridLength(1, GridUnitType.Star);
                    _vm.MediaPlayerMinHeight = 1000;
                }
            };
        };

        ScanFolderCheckBox.IsCheckedChanged += (s, e) =>
        {
            if (ScanFolderCheckBox.IsChecked == true)
                AppData.Settings.ScanFolderOnStartup = true;
            else
                AppData.Settings.ScanFolderOnStartup = false;
        };
    }

    private async void MediaDoubleClick(object? sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is Border { DataContext: DownloadedMedia media })
            {
                if (!File.Exists(media.DownloadPath))
                {
                    media.IsPlayable = false;
                    throw new Exception("Media not found");
                }

                //TODO: NEW Mediaplayer logic
            }
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            
        }
    }

    private async void CopyStringToClipboard(string text)
    {
        try
        {
            var clipboard = GetTopLevel(this)?.Clipboard;
            if (clipboard == null) throw new Exception("Clipboard is not available");
            await clipboard.SetTextAsync(text);
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while trying to copy: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await _ds.ShowAlertAsync("An error occurred while trying to copy: " + ex.Message);
        }
    }

    private void CopyDownloadPathClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
            CopyStringToClipboard(media.DownloadPath);
    }

    private void CopyUrlClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
            CopyStringToClipboard(media.Url);
    }

    private async void DeleteMedia(object sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is MenuItem { DataContext: DownloadedMedia media })
            {
                var result = await _ds.ConfirmAsync("Are you sure you want to remove this media from the list? This action cannot be undone");
                if (!result) return;

                AppData.RemoveDownloadedMedia(media);

                await Database.DeleteDownloadedMedia(media.Identifier);

                var log = new Message("Media removed: " + media.Url, DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await _ds.ShowAlertAsync("Media removed from the list: " + media.Url);
            }
        }
        catch (Exception ex)
        {
            var log = new Message("Error removing media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await _ds.ShowAlertAsync("An error occured while trying to remove the media: " + ex.Message);
        }
    }

    private async void DeleteFile(object sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is MenuItem { DataContext: DownloadedMedia media })
            {
                var result = await _ds.ConfirmAsync("Are you sure you want to delete the file? This action cannot be undone.");

                if (result && File.Exists(media.DownloadPath))
                {
                    File.Delete(media.DownloadPath);
                    media.IsPlayable = false;

                    var log = new Message("File deleted: " + media.DownloadPath, DateTime.Now, "INFO");
                    _logger.LogNewMassage(log);

                    await _ds.ShowAlertAsync("File deleted: " + media.DownloadPath);
                }
                else
                {
                    throw new Exception("File not found");
                }
            }
        }
        catch (Exception ex)
        {
            var log = new Message("Error deleting file: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await _ds.ShowAlertAsync("An error occured while trying to delete the file: " + ex.Message);
        }
    }

    private void PlaylistDoubleClick(object? sender, RoutedEventArgs e)
    {
        if (sender is Border { DataContext: Playlist playlist })
        {
            var playlistWindow = new PlaylistDetailsWindow(playlist);
            playlistWindow.Show();
        }
    }

    private void OpenPlaylistDetailsClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: Playlist playlist })
        {
            var playlistWindow = new PlaylistDetailsWindow(playlist);
            playlistWindow.Show();
        }
    }

    private async void DeletePlaylist(object sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is MenuItem { DataContext: Playlist playlist })
            {
                AppData.RemovePlaylist(playlist);

                var log = new Message("Playlist removed: " + playlist.Name, DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await _ds.ShowAlertAsync("Playlist removed: " + playlist.Name);
            }
        }
        catch (Exception ex)
        {
            var log = new Message("Error removing playlist: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            await _ds.ShowAlertAsync("An error occured while trying to remove the playlist: " + ex.Message);
        }
    }

    private async void AddToPlaylistClick(object? sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is not ListBox { SelectedItem: Playlist playlist } listBox) return;
            if (listBox.DataContext is not DownloadedMedia media) return;

            await playlist.AddNewMedia(media.Identifier);
            listBox.SelectedItem = null;

            await _ds.ShowAlertAsync($"Added {media.Title} to {playlist.Name}");

            var log = new Message($"Added {media.Title} to {playlist.Name}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
        }
        catch (Exception ex)
        {
            var log = new Message("An error occured while trying to add media to playlist: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await _ds.ShowAlertAsync("An error occured while trying to add media to playlist: " + ex.Message);
        }
    }
}
