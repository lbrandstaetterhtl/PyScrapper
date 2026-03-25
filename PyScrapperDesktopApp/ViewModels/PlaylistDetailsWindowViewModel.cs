using System;
using System.Collections.Generic;
using System.Linq;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// PlaylistDetailsWindowViewModel is a view model class that manages the data and commands for the playlist details window in the PyScrapperDesktopApp.
/// It allows users to view the details of a playlist, including its name, description, and the media items it contains.
/// The view model also provides commands to cancel the operation and to play the playlist.
/// When the play command is executed, it checks for playable media items in the playlist and handles the playback accordingly.
/// If no playable media is found, it displays a message box to inform the user.
/// </summary>
public partial class PlaylistDetailsWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _playlistName = string.Empty;
    
    [ObservableProperty]
    private string _description = string.Empty;
    
    [ObservableProperty]
    private List<DownloadedMedia> _medias = new List<DownloadedMedia>();
    
    [ObservableProperty]
    private int _playlistId;
    
    public readonly Playlist _playlist;
    
    /// <summary>
    /// Constructor for the PlaylistDetailsWindowViewModel class, which initializes the view model with the details of a given playlist. It sets the playlist name, description, and media items based on the provided playlist object.
    /// The constructor also assigns the playlist to a private field for later use in command methods.
    /// </summary>
    /// <param name="playlist"></param>
    public PlaylistDetailsWindowViewModel(Playlist playlist)
    {
        PlaylistName = playlist.Name;
        Description = playlist.Description;
        PlaylistId = playlist.Id;
        Medias = AppData.DownloadedMedias.Where(m => playlist.MediaIds.Contains(m.Id)).ToList();
        _playlist = playlist;
    }
    
    public void RefreshMedias()
    {
        Medias = AppData.DownloadedMedias.Where(m => _playlist.MediaIds.Contains(m.Id)).ToList();
    }
    
    public Action? CloseRequested { get; set; }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "Cancel" button in the playlist details window.
    /// It triggers the CloseRequested action, which can be handled by the view to close the window.
    /// This allows users to exit the playlist details view without making any changes or starting playback.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "Play Playlist" button in the playlist details window.
    /// It checks if the application is running in a desktop environment and then retrieves the list of playable media items that are part of the playlist.
    /// If no playable media is found, it displays a message box to inform the user.
    /// If playable media is found, it would proceed to handle the playback of those media items (the actual playback logic is not implemented in this snippet and would need to be added based on the application's media player implementation).
    /// This allows users to easily play all the media items in the playlist directly from the playlist details view.
    /// </summary>
    [RelayCommand]
    private void PlayPlaylist()
    {
        if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
        {
            return;
        }
        
        if (_playlist.PlayableMediaIds.Count == 0)
        {
            var messageBox = new MessageBox("No playable media found in this playlist.");
            messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
        
        var mediaPlayerWindow = new MediaPlayerWindow(playlist: _playlist);
        mediaPlayerWindow.Show();
    }
}