using System;
using System.Collections.Generic;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// CreatePlaylistWindowViewModel is a view model class that manages the state and behavior of the CreatePlaylistWindow in the PyScrapperDesktopApp.
/// </summary>
public partial class CreatePlaylistWindowViewModel : ObservableObject
{
    private readonly Window _createPlaylistWindow;
    
    [ObservableProperty]
    private string _playlistName;
    
    private readonly List<int> _selectedMediaIds;
    
    [ObservableProperty]
    private List<DownloadedMedia> _selectedMedias;
    
    [ObservableProperty]
    private List<DownloadedMedia> _availableMedias;
    
    [ObservableProperty]
    private string? _description;
    
    /// <summary>
    /// Constructor for the CreatePlaylistWindowViewModel class, which initializes the view model with the provided create playlist window.
    /// It sets up the available medias from the application's downloaded medias and initializes the selected medias and media IDs lists.
    /// The constructor also assigns the provided window to a private field for later use in displaying message boxes.
    /// </summary>
    /// <param name="createPlaylistWindow"></param>
    public CreatePlaylistWindowViewModel(Window createPlaylistWindow)
    {
        AvailableMedias = new List<DownloadedMedia>(AppData.DownloadedMedias);
        SelectedMedias = new List<DownloadedMedia>();
        _selectedMediaIds = new List<int>();
        _createPlaylistWindow = createPlaylistWindow;
    }
    
    public Action? CloseRequested { get; set; }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "Create Playlist" button.
    /// It validates the playlist name, collects the selected media IDs, creates a new playlist with the provided name and description, and adds it to the application's playlist data.
    /// </summary>
    [RelayCommand]
    private void CreatePlaylist()
    {
        if (string.IsNullOrWhiteSpace(PlaylistName))
        {
            var messageBox = new MessageBox("Playlist name cannot be empty.");
            messageBox.ShowDialog(_createPlaylistWindow);
            return;
        }
        
        _selectedMediaIds.Clear();
        foreach (var media in SelectedMedias)
        {
            _selectedMediaIds.Add(media.Id);
        }
        
        var newPlaylist = new Playlist(_selectedMediaIds, PlaylistName, Description ?? "");
        newPlaylist.SetHighestId(AppData.Playlists);
        newPlaylist.SetPlayableMediaIds(AppData.PlayableMedias);
        
        AppData.AddPlaylist(newPlaylist);
        
        var messagebox = new MessageBox("Playlist created successfully!");
        messagebox.ShowDialog(_createPlaylistWindow);
        
        SelectedMedias = new List<DownloadedMedia>();
        PlaylistName = string.Empty;
        Description = string.Empty;
    }

    /// <summary>
    /// Cancel command method that is executed when the user clicks the "Cancel" button.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}