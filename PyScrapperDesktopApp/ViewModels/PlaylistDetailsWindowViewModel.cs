using System;
using System.Collections.Generic;
using System.Linq;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

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
    
    private readonly Playlist _playlist;
    
    public PlaylistDetailsWindowViewModel(Playlist playlist)
    {
        PlaylistName = playlist.Name;
        Description = playlist.Description;
        PlaylistId = playlist.Id;
        Medias = AppData.DownloadedMedias.Where(m => playlist.MediaIds.Contains(m.Id)).ToList();
        _playlist = playlist;
    }
    
    public Action? CloseRequested { get; set; }
    
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
    
    [RelayCommand]
    private void PlayPlaylist()
    {
        if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
        {
            return;
        }
        
        var playableMedias = AppData.PlayableMedias.Where(m => _playlist.PlayableMediaIds.Contains(m.Id)).ToList();
        
        if (playableMedias.Count == 0)
        {
            var messageBox = new MessageBox("No playable media found in this playlist.");
            messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
        
        foreach (var media in playableMedias)
        {
        }
    }
}