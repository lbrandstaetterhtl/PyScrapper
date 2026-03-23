using System;
using System.Collections.Generic;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

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
    
    public CreatePlaylistWindowViewModel(Window createPlaylistWindow)
    {
        AvailableMedias = new List<DownloadedMedia>(AppData.DownloadedMedias);
        SelectedMedias = new List<DownloadedMedia>();
        _selectedMediaIds = new List<int>();
        _createPlaylistWindow = createPlaylistWindow;
    }
    
    public Action? CloseRequested { get; set; }
    
    [RelayCommand]
    private void CreatePlaylist()
    {
        if (string.IsNullOrWhiteSpace(PlaylistName))
        {
            var messageBox = new MessageBox("Playlist name cannot be empty.");
            messageBox.ShowDialog(_createPlaylistWindow);
            return;
        }
        
        foreach (var media in SelectedMedias)
        {
            _selectedMediaIds.Add(media.Id);
        }
        
        var newPlaylist = new Playlist(_selectedMediaIds, PlaylistName, Description);
        newPlaylist.SetHighestId(AppData.Playlists);
        newPlaylist.SetPlayableMediaIds(AppData.PlayableMedias);
        
        AppData.AddPlaylist(newPlaylist);
        
        var messagebox = new MessageBox("Playlist created successfully!");
        messagebox.ShowDialog(_createPlaylistWindow);
        
        SelectedMedias = new List<DownloadedMedia>();
        PlaylistName = string.Empty;
        Description = string.Empty;
    }

    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}