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
    
    [ObservableProperty]
    private string _playlistName;
    
    [ObservableProperty]
    private List<DownloadedMedia> _selectedMedias;
    
    [ObservableProperty]
    private List<DownloadedMedia> _availableMedias;
    
    [ObservableProperty]
    private string? _description;

    private DialogService _dialogService;
    
    /// <summary>
    /// Constructor for the CreatePlaylistWindowViewModel class, which initializes the view model with the provided create playlist window.
    /// It sets up the available medias from the application's downloaded medias and initializes the selected medias and media IDs lists.
    /// The constructor also assigns the provided window to a private field for later use in displaying message boxes.
    /// </summary>
    /// <param name="createPlaylistWindow"></param>
    public CreatePlaylistWindowViewModel(DialogService dialogService)
    {
        AvailableMedias = new List<DownloadedMedia>(AppData.DownloadedMedias);
        SelectedMedias = new List<DownloadedMedia>();
        _dialogService = dialogService;
    }
    
    public Action? CloseRequested { get; set; }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "Create Playlist" button.
    /// It validates the playlist name, collects the selected media IDs, creates a new playlist with the provided name and description, and adds it to the application's playlist data.
    /// </summary>
    [RelayCommand]
    private async void CreatePlaylist()
    {
        if (string.IsNullOrWhiteSpace(PlaylistName))
        {
            await _dialogService.ShowAlertAsync("Playlist name cannot be empty.");
            return;
        }

        var req = new CreatePlaylistRequest()
        {
            Name = PlaylistName,
            Description = Description ?? string.Empty,
            UserIdentifier = AppData.CurrentUser.Identifier
        };

        var newPlaylist = await Database.CreatePlaylist(req);
        
        AppData.AddPlaylist(newPlaylist);
        
        await _dialogService.ShowAlertAsync("Playlist created successfully!");

        foreach (var media in SelectedMedias)
        {
            var reqMedia = new CreatePlaylistMediaRequest()
            {
                PlaylistIdentifier = newPlaylist.Identifier,
                MediaIdentifier = media.Identifier
            };
            
            var newPlaylistMedia = await Database.CreatePlaylistMedia(reqMedia);
            
            AppData.PlaylistMedias.Add(newPlaylistMedia);
        }
        
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