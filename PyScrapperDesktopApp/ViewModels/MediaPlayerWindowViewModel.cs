using System;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MediaPlayerWindowViewModel : ObservableObject, IDisposable
{
    public readonly AudioPlayer _audioPlayer = new();
    
    private Window? _mediaPlayerWindow;

    [ObservableProperty]
    private int _volume = 70;
    
    [ObservableProperty]
    private string _nowPlayingTitle = "No media loaded";
    
    [ObservableProperty]
    private double _positionSeconds;
    
    [ObservableProperty]
    private double _durationSeconds;
    
    [ObservableProperty]
    private bool _hasVideo;
    
    [ObservableProperty]
    private bool _isShuffleEnabled;
    
    public string CurrentlyText => TimeSpan.FromSeconds(PositionSeconds).ToString(@"mm\:ss");
    public string DurationText => TimeSpan.FromSeconds(DurationSeconds).ToString(@"mm\:ss");
    
    public MediaPlayer MediaPlayer => _audioPlayer.MediaPlayer;
    
    public event EventHandler<bool>? VideoAvailableChanged;

    public MediaPlayerWindowViewModel()
    {
        _audioPlayer.TrackChanged += (s, title) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                NowPlayingTitle = title ?? "Unknown Title";
            });
            
        };
        
        _audioPlayer.VideoAvailableChanged += (s, hasVideo) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                HasVideo = hasVideo;
                VideoAvailableChanged?.Invoke(this, hasVideo);
            });
        };

        _audioPlayer.MediaPlayer.VolumeChanged += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                Volume = (int)e.Volume;
            });
        };
        
        _audioPlayer.MediaPlayer.TimeChanged += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                PositionSeconds = e.Time / 1000.0;
                OnPropertyChanged(nameof(CurrentlyText));
            });
        };

        _audioPlayer.MediaPlayer.LengthChanged += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                DurationSeconds = e.Length / 1000.0;
                OnPropertyChanged(nameof(DurationText));
            });
        };
        
        _audioPlayer.MediaPlayer.Volume = Volume;
    }
    
    public void OnVideoViewReady(Window mediaPlayerWindow)
    {
        _mediaPlayerWindow = mediaPlayerWindow;
    }
    
    partial void OnIsShuffleEnabledChanged(bool value)
    {
        _audioPlayer.ToggleShuffle();
    }
    
    [RelayCommand]
    private void Play() => _audioPlayer.MediaPlayer.Play();
 
    [RelayCommand]
    private void Pause() => _audioPlayer.MediaPlayer.Pause();

    [RelayCommand]
    private void Stop()
    {
        _audioPlayer.Stop();
        
        PositionSeconds = 0;
        DurationSeconds = 0;
        OnPropertyChanged(nameof(CurrentlyText));
        OnPropertyChanged(nameof(DurationText));
    }

    [RelayCommand]
    private void PlayNext() => _audioPlayer.PlayNext();
 
    [RelayCommand]
    private void PlayPrevious() => _audioPlayer.PlayPrevious();
 
    [RelayCommand]
    private void MoveForward() => _audioPlayer.MediaPlayer.Time += 10_000;
 
    [RelayCommand]
    private void MoveBackward() => _audioPlayer.MediaPlayer.Time -= 10_000;
 
    [RelayCommand]
    private void IncreaseVolume() =>
        _audioPlayer.MediaPlayer.Volume = Math.Min(100, _audioPlayer.MediaPlayer.Volume + 5);
 
    [RelayCommand]
    private void DecreaseVolume() =>
        _audioPlayer.MediaPlayer.Volume = Math.Max(0, _audioPlayer.MediaPlayer.Volume - 5);

    [RelayCommand]
    private async Task OpenFiles()
    {
        if (_mediaPlayerWindow is null) return;

        var files = await _mediaPlayerWindow.StorageProvider.OpenFilePickerAsync(
            new FilePickerOpenOptions
            {
                Title = "Open Media Files",
                AllowMultiple = false,
                FileTypeFilter =
                [
                    new FilePickerFileType("Audio/Video")
                    {
                        Patterns = ["*.mp3", "*.mp4", "*.avi", "*.mkv", "*.flac", "*.wav"]
                    }
                ]
            }
        );

        if (files.Count <= 0)
        {
            var messageBox = new MessageBox("No file selected.");
            await messageBox.ShowDialog(_mediaPlayerWindow);
            return;
        }
        
        _audioPlayer.PlayFile(files.Select(f => f.Path.LocalPath).First());
    }
    
    public void LoadPlaylist(Playlist playlist)
    {
        _audioPlayer.LoadPlaylist(playlist);
    }
    
    public void Dispose()
    {
        _audioPlayer.Dispose();
    }
}