using System;
using System.IO;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MediaPlayerControlViewModel : ObservableObject, IDisposable
{
    private AudioPlayer _audioPlayer = null;

    [ObservableProperty] private int _volume = 70;
    [ObservableProperty] private string _nowPlayingTitle = "No media loaded";
    [ObservableProperty] private double _positionSeconds;
    [ObservableProperty] private double _durationSeconds;
    [ObservableProperty] private bool _hasVideo;
    [ObservableProperty] private bool _isShuffleEnabled;
    [ObservableProperty] private bool _isPlaylistMode;
    [ObservableProperty] private bool _hasNext;
    [ObservableProperty] private bool _hasPrevious;
    [ObservableProperty] private bool _isCompact = true;
    [ObservableProperty] private double _videoHeight;
    [ObservableProperty] private double _videoWidth;
    public float AspectRatio { get; private set; } = 0;

    // IsNormalView = nicht kompakt
    public bool IsNormalView => !IsCompact;

    // Event für Code-behind — VideoView verknüpfen nach Layout-Pass
    public event EventHandler? CompactClosed;
    public event EventHandler? CompactOpened;

    private static bool DarkMode => AppData.Settings.DarkModeEnabled;

    public Bitmap VolumeIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "volume-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "volume-lightmode.png"));

    public Bitmap SongIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "song-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "song-lightmode.png"));

    public Bitmap PlayIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "play-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "play-lightmode.png"));

    public Bitmap PauseIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "pause-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "pause-lightmode.png"));

    public Bitmap ForwardIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "forward-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "forward-lightmode.png"));

    public Bitmap BackIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "backward-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "backward-lightmode.png"));

    public Bitmap ShuffleIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "shuffle-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "shuffle-lightmode.png"));
    
    public Bitmap ArrowUpIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "arrow-up-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "arrow-up-lightmode.png"));
    
    public Bitmap ArrowDownIcon => DarkMode
        ? new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "DarkMode", "arrow-down-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "MediaPlayer", "LightMode", "arrow-down-lightmode.png"));
    
    public Bitmap ToggleCompactIcon => IsCompact ? ArrowUpIcon : ArrowDownIcon;

    public bool VolumeSliderMoving { get; set; }
    public bool SeekSliderMoving { get; set; }

    public string CurrentlyText => TimeSpan.FromSeconds(PositionSeconds).ToString(@"mm\:ss");
    public string DurationText  => TimeSpan.FromSeconds(DurationSeconds).ToString(@"mm\:ss");

    public MediaPlayer MediaPlayer;

    public event EventHandler<bool>? VideoAvailableChanged;
    private readonly AppLogger _logger = AppLogger.Instance;
    private bool _volumeInitialized = false;
    private Playlist _playlist;

    public MediaPlayerControlViewModel()
    {
        SetAudioPlayer();
    }

    public void SetSeekValue(long value)
    {
        _audioPlayer.MediaPlayer.Time = value * 1000;
    }

    public void SetVolume(double volume)
    {
        _audioPlayer.MediaPlayer.Volume = (int)volume;
    }

    public void VideoViewLoaded(Playlist playlist = null)
    {
        _playlist = playlist;
        if (_playlist != null)
        {
            LoadPlaylist(_playlist);
            HasNext = _audioPlayer.HasNext;
            HasPrevious = _audioPlayer.HasPrevious;
            IsPlaylistMode = _audioPlayer.PlaylistModeEnabled;
            MediaPlayer = _audioPlayer.MediaPlayer;
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
                NowPlayingTitle = Path.GetFileNameWithoutExtension(path) ?? "Unknown Title";
                HasNext = _audioPlayer.HasNext;
                HasPrevious = _audioPlayer.HasPrevious;
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
            
            uint videoWidth = 0, videoHeight = 0;
            _audioPlayer.MediaPlayer.Size(0, ref videoWidth, ref videoHeight);

            if (videoWidth > 0 && videoHeight > 0)
            {
                AspectRatio = (float)videoWidth / videoHeight;
            }
        };
        
        _audioPlayer.VideoAvailableChanged += (s, hasVideo) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                HasVideo = hasVideo;
            });
        };

        MediaPlayer = _audioPlayer.MediaPlayer;
    }

    partial void OnIsShuffleEnabledChanged(bool value)
    {
        _audioPlayer.ToggleShuffle();
    }

    public void Play()  => _audioPlayer.MediaPlayer.Play();
    public void Pause() => _audioPlayer.MediaPlayer.Pause();

    [RelayCommand]
    private void Stop()
    {
        _audioPlayer.Stop();
        PositionSeconds = 0;
        DurationSeconds = 0;
        OnPropertyChanged(nameof(CurrentlyText));
        OnPropertyChanged(nameof(DurationText));
    }

    [RelayCommand] private void PlayNext()     => _audioPlayer.PlayNext();
    [RelayCommand] private void PlayPrevious() => _audioPlayer.PlayPrevious();
    [RelayCommand] private void MoveForward()  => _audioPlayer.MediaPlayer.Time += 10_000;
    [RelayCommand] private void MoveBackward() => _audioPlayer.MediaPlayer.Time -= 10_000;

    [RelayCommand]
    private void IncreaseVolume()
    {
        Volume = Math.Min(100, Volume + 5);
        _audioPlayer.MediaPlayer.Volume = Volume;
    }

    [RelayCommand]
    private void DecreaseVolume()
    {
        Volume = Math.Max(0, Volume - 5);
        _audioPlayer.MediaPlayer.Volume = Volume;
    }

    public void LoadPlaylist(Playlist playlist)
    {
        SetAudioPlayer();
        _audioPlayer.LoadPlaylist(playlist);
        IsPlaylistMode = _audioPlayer.PlaylistModeEnabled;
    }

    [RelayCommand]
    private void ToggleCompact()
    {
        IsCompact = !IsCompact;
        OnPropertyChanged(nameof(IsNormalView));
        

        if (!IsCompact)
            CompactClosed?.Invoke(this, EventArgs.Empty);
        else
            CompactOpened?.Invoke(this, EventArgs.Empty);
    }

    public void Dispose()
    {
        _audioPlayer.Dispose();
    }
}