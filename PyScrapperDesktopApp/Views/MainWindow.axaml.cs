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
    private readonly AppLogger _logger = new();
    private int _mediaHideCounter = 0;
    private int _playlistHideCounter = 0;
    
    public MainWindow()
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);

        _vm = new MainWindowViewModel();
        
        DataContext = _vm;
        
        _vm.UpdateHideIcon();

        Opened += (s, e) =>
        {
            _vm.OnWindowReady(this);
        };

        MediaHide.Click += (s, e) =>
        {
            _mediaHideCounter++;
            MediasGrid.IsVisible = _mediaHideCounter % 2 == 0;
            FirstSplitter.IsVisible = _mediaHideCounter % 2 == 0;
            _vm.UpdateHideIcon();
        };

        PlaylistHide.Click += (s, e) =>
        {
            _playlistHideCounter++;
            PlaylistsGrid.IsVisible = _playlistHideCounter % 2 == 0;
            LastSplitter.IsVisible = _playlistHideCounter % 2 == 0;
            _vm.UpdateHideIcon();
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

                List<int> mediaIds = [media.Id];
                Playlist playlist = new Playlist(mediaIds, "NPLL", "");
                
                MediaPlayer.LoadAndPlay(playlist);
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while trying to play the media: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }

    private async void CopyStringToClipboard(string text)
    {
        try
        {
            var clipboard = GetTopLevel(this)?.Clipboard;

            if (clipboard == null)
            {
                throw new Exception("Clipboard is not available");
            }
            
            await clipboard.SetTextAsync(text);
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to copy the download path: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while trying to copy the download path: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }
    
    private void CopyDownloadPathClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            CopyStringToClipboard(media.DownloadPath);
        }
    }
    
    private void CopyUrlClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            CopyStringToClipboard(media.Url);
        }
    }
    
    private async void DeleteMedia(object sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is MenuItem { DataContext: DownloadedMedia media })
            {
                var confirmationWindow =
                    new ConfirmationWindow(
                        "Are you sure you want to remove this media from the list? This action cannot be undone.");
                var result = await confirmationWindow.ShowDialog<bool>(this);

                if (!result) return;

                AppData.RemoveDownloadedMedia(media);
                var playlistContained = AppData.Playlists.Where(p => p.MediaIds.Contains(media.Id)).ToList();

                foreach (var playlist in playlistContained)
                {
                    playlist.RemoveMedia(media.Id);
                }

                var log = new Massage("Media removed from the list: " + media.Url, DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                var messageBox = new MessageBox("Media removed from the list: " + media.Url);
                await messageBox.ShowDialog(this);
            }
        }
        catch (Exception ex)
        {
            var lag = new Massage("An error occurred while trying to remove the media from the list: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(lag);
            
            var messageBox = new MessageBox("An error occurred while trying to remove the media from the list: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }
    
    private async void DeleteFile(object sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is MenuItem { DataContext: DownloadedMedia media })
            {
                var confirmationWindow =
                    new ConfirmationWindow("Are you sure you want to delete the file? This action cannot be undone.");
                var result = await confirmationWindow.ShowDialog<bool>(this);

                if (result && File.Exists(media.DownloadPath))
                {
                    File.Delete(media.DownloadPath);

                    media.IsPlayable = false;

                    var log = new Massage("File deleted successfully: " + media.DownloadPath, DateTime.Now, "INFO");
                    _logger.LogNewMassage(log);

                    var messageBox = new MessageBox("File deleted successfully: " + media.DownloadPath);
                    messageBox.ShowDialog(this);
                }
                else
                {
                    throw new Exception("File not found");
                }
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to delete the file: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
                
            var messageBox = new MessageBox("An error occurred while trying to delete the file: " + ex.Message);
            await messageBox.ShowDialog(this);
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
    
    private void DeletePlaylist(object sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: Playlist playlist })
        {
            AppData.RemovePlaylist(playlist);
            
            var log = new Massage("Playlist removed from the list: " + playlist.Name, DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("Playlist removed from the list: " + playlist.Name);
            messageBox.ShowDialog(this);
        }
    }
    
    private void AddToPlaylistClick(object? sender, RoutedEventArgs e)
    {
        if (sender is not ListBox { SelectedItem: Playlist playlist } listBox) return;
        if (listBox.DataContext is not DownloadedMedia media) return;

        playlist.AddMedia(media.Id);
        listBox.SelectedItem = null;
        
        var messageBox = new MessageBox($"Added {media.Title} to {playlist.Name}");
        messageBox.ShowDialog(this);
    
        var log = new Massage($"Added {media.Title} to {playlist.Name}", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
    }
}