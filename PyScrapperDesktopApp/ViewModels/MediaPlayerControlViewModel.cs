using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// ViewModel for the MediaPlayerWindow, responsible for managing the state and logic of the media player interface. It interacts with the AudioPlayer model to control media playback, update UI elements such as the current track title, playback position, duration, and volume. The ViewModel also handles user interactions through commands for play, pause, stop, next, previous, volume adjustments, and seeking within the media. It raises events when video availability changes to allow the view to respond accordingly.
/// Additionally, it manages playlist loading and shuffle mode toggling when applicable.
/// </summary>
public partial class MediaPlayerControlViewModel : ObservableObject, IDisposable
{
    private AudioPlayer _audioPlayer = null;

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
    
    [ObservableProperty]
    private bool _isPlaylistMode;

    [ObservableProperty] 
    private bool _hasNext;

    [ObservableProperty]
    private bool _hasPrevious;
    
    private static bool DarkMode => AppData.Settings.DarkModeEnabled;

    public Bitmap VolumeIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "volume-darkmode.png")) 
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "volume-lightmode.png"));
    
    public Bitmap SongIcon => DarkMode 
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "song-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "song-lightmode.png"));

    public Image PlayIcon => new Image
    {
        Source = DarkMode 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "play-darkmode.png"))
            : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "play-lightmode.png"))
    };

    public Image ForwardIcon => new Image
    {
        Source = DarkMode 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "forward-darkmode.png"))
            : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "forward-lightmode.png"))
    };

    public Image BackIcon => new Image
    {
        Source = DarkMode 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "backward-darkmode.png"))
            : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "backward-lightmode.png"))
    };
    
    public Image PauseIcon => new Image
    {
        Source = DarkMode 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "pause-darkmode.png"))
            : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "pause-lightmode.png"))
    };

    public Image ShuffleIcon => new Image
    {
        Source = DarkMode 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "shuffle-darkmode.png"))
            : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "shuffle-lightmode.png")),
    };
    
    public bool VolumeSliderMoving { get; set; }
    public bool SeekSliderMoving { get; set; }

    public string CurrentlyText => TimeSpan.FromSeconds(PositionSeconds).ToString(@"mm\:ss");

    public string DurationText => TimeSpan.FromSeconds(DurationSeconds).ToString(@"mm\:ss");
    
    public MediaPlayer MediaPlayer => _audioPlayer.MediaPlayer;
    
    public event EventHandler<bool>? VideoAvailableChanged;
    private readonly AppLogger _logger = new();
    private bool _volumeInitialized = false;

    private  Playlist _playlist;
    
    /// <summary>
    /// Constructor for the MediaPlayerWindowViewModel, which initializes the view model with an optional playlist.
    /// It sets up event handlers for media playback events such as playing, track changes, video availability changes, time changes, and length changes.
    /// The constructor also initializes the AudioPlayer instance and configures it to update the UI elements accordingly when these events occur.
    /// If a playlist is provided, it will be loaded when the video view is loaded.
    /// </summary>
    /// <param name="playlist"></param>
    public MediaPlayerControlViewModel()
    {
       SetAudioPlayer();
    }

    /// <summary>
    /// Sets the current playback position of the media player based on the provided value in seconds.
    /// The value is converted to milliseconds before being assigned to the MediaPlayer's Time property, allowing for seeking within the media.
    /// </summary>
    /// <param name="value"></param>
    public void SetSeekValue(long value)
    {
        _audioPlayer.MediaPlayer.Time = (value * 1000);
    }

    /// <summary>
    /// Sets the volume of the media player based on the provided value, which is expected to be in the range of 0 to 100.
    /// The value is cast to an integer and assigned to the MediaPlayer's Volume property, allowing for volume adjustments.
    /// </summary>
    /// <param name="volume"></param>
    public void SetVolume(double volume)
    {
        _audioPlayer.MediaPlayer.Volume = (int)volume;
    }

    /// <summary>
    /// Method to be called when the video view is loaded, which checks if a playlist is available and loads it into the audio player.
    /// It also updates the HasNext, HasPrevious, and IsPlaylistMode properties based on the state of the audio player after loading the playlist.
    /// </summary>
    public void VideoViewLoaded()
    {
        if (_playlist != null)
        {
            LoadPlaylist(_playlist);
            HasNext = _audioPlayer.HasNext;
            HasPrevious = _audioPlayer.HasPrevious;
            IsPlaylistMode = _audioPlayer.PlaylistModeEnabled;
        }
    }

    private void SetAudioPlayer()
    {
        if (_audioPlayer != null) _audioPlayer?.Dispose();
        
        _audioPlayer = new AudioPlayer();
        
        _audioPlayer.MediaPlayer.Playing += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                _audioPlayer.MediaPlayer.Volume = Volume;
            });
        };
        
        _audioPlayer.TrackChanged += (s, path) =>
        {
            _volumeInitialized = false;
            
            Dispatcher.UIThread.Post(() =>
            {
                var title = Path.GetFileNameWithoutExtension(path);
                NowPlayingTitle = title ?? "Unknown Title";
                HasNext = _audioPlayer.HasNext;
                HasPrevious = _audioPlayer.HasPrevious;
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
        
        _audioPlayer.MediaPlayer.TimeChanged += (s, e) =>
        {
            if (!_volumeInitialized)
            {
                _volumeInitialized = true;
                _audioPlayer.MediaPlayer.Volume = Volume;
            }
            
            if (!SeekSliderMoving)
            {
                Dispatcher.UIThread.Post(() =>
                {
                    PositionSeconds = e.Time / 1000.0;
                    OnPropertyChanged(nameof(CurrentlyText));
                });
            }
        };

        _audioPlayer.MediaPlayer.LengthChanged += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                DurationSeconds = e.Length / 1000.0;
                OnPropertyChanged(nameof(DurationText));
            });
        };
    }
    
    /// <summary>
    /// Method that is called when the IsShuffleEnabled property changes, which toggles the shuffle mode of the audio player.
    /// </summary>
    /// <param name="value"></param>
    partial void OnIsShuffleEnabledChanged(bool value)
    {
        _audioPlayer.ToggleShuffle();
    }
    
    public void Play() => _audioPlayer.MediaPlayer.Play();
 
    public void Pause() => _audioPlayer.MediaPlayer.Pause();

    /// <summary>
    /// Stops the media playback and resets the position and duration to zero.
    /// It also raises property changed notifications for the CurrentlyText and DurationText properties to update the UI accordingly.
    /// </summary>
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

    /// <summary>
    /// Increases the volume of the media player by 5 units, ensuring that it does not exceed the maximum volume of 100.
    /// It updates the Volume property and sets the MediaPlayer's Volume accordingly to reflect the change in the UI and the actual audio output.
    /// </summary>
    [RelayCommand]
    private void IncreaseVolume()
    {
        Volume = Math.Min(100, Volume + 5);
        _audioPlayer.MediaPlayer.Volume = Volume;
    }

    /// <summary>
    /// Decreases the volume of the media player by 5 units, ensuring that it does not go below the minimum volume of 0.
    /// It updates the Volume property and sets the MediaPlayer's Volume accordingly to reflect the change in the UI and the actual audio output.
    /// </summary>
    [RelayCommand]
    private void DecreaseVolume()
    {
        Volume = Math.Max(0, Volume - 5);
        _audioPlayer.MediaPlayer.Volume = Volume;
    }
    
    /// <summary>
    /// Loads a playlist into the audio player, allowing for the playback of multiple media items in a specified order.
    /// The method takes a Playlist object as a parameter and uses the LoadPlaylist method of the AudioPlayer to set up the playlist for playback.
    /// </summary>
    /// <param name="playlist"></param>
    public void LoadPlaylist(Playlist playlist)
    {
        SetAudioPlayer();
        _audioPlayer.LoadPlaylist(playlist);
        IsPlaylistMode = _audioPlayer.PlaylistModeEnabled;
    }
    
    /// <summary>
    /// Disposes of the resources used by the MediaPlayerWindowViewModel, specifically by calling the Dispose method of the AudioPlayer instance to release any unmanaged resources and clean up the media player properly when the view model is no longer needed.
    /// </summary>
    public void Dispose()
    {
        _audioPlayer.Dispose();
    }
}