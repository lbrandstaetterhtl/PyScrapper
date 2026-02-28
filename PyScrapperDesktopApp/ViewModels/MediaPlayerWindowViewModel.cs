// C#
using System;
using System.IO;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MediaPlayerWindowViewModel : ObservableObject, IDisposable
{
    private readonly AppLogger _logger = new();
    public readonly AudioPlayer _audioPlayer;
    private readonly DispatcherTimer _timer;
    private DateTime _suppressPlayerUpdateUntil = DateTime.MinValue;
    private double? _lastRequestedPositionSeconds = null;

    [ObservableProperty]
    private bool isScrubbing;

    [ObservableProperty]
    private string nowPlayingTitle = "No media loaded";

    [ObservableProperty]
    private double positionSeconds;

    [ObservableProperty]
    private double durationSeconds;

    [ObservableProperty]
    private int volume = 70;

    [ObservableProperty]
    private string currentlyText = "0:00";

    [ObservableProperty]
    private string durationText = "0:00";

    public MediaPlayerWindowViewModel(AudioPlayer audioPlayer, string path)
    {
        _audioPlayer = audioPlayer;

        _audioPlayer.Volume = volume;

        // langsameres Polling, glättet UI-Updates weiter
        _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
        _timer.Tick += (s, e) => RefreshFromPlayer();
        _timer.Start();

        _audioPlayer.Open(path);

        var massage = new Massage("audio player opened " + Path.GetFileName(path), DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);

        _audioPlayer.Play();

        massage = new Massage("audio player started playing", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    [RelayCommand] public void Play()
    {
        _audioPlayer.Play();
        var massage = new Massage("audio player started playing", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    [RelayCommand] public void Pause()
    {
        _audioPlayer.Pause();
        var massage = new Massage("audio player paused", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    [RelayCommand] public void Stop()
    {
        _audioPlayer.Stop();
        var massage = new Massage("audio player stopped", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    [RelayCommand]
    public void BeginScrub()
    {
        IsScrubbing = true;
    }

    [RelayCommand]
    public void ScrubTo(double seconds)
    {
        _audioPlayer.Pause();
        PositionSeconds = Math.Max(0, seconds);

        CurrentlyText = FormatTime((long)Math.Round(PositionSeconds));
        if (DurationSeconds > 0)
        {
            var remaining = Math.Max(0, DurationSeconds - PositionSeconds);
            DurationText = "-" + FormatTime((long)Math.Round(remaining));
        }
        else
        {
            DurationText = "-0:00";
        }
    }

    [RelayCommand]
    public void EndScrub()
    {
        SeekToSeconds(PositionSeconds);
        IsScrubbing = false;
        _audioPlayer.Play();
    }

    public void SeekToSeconds(double seconds)
    {
        _audioPlayer.Pause();
        var ms = (long)(Math.Max(0, seconds) * 1000.0);
        _audioPlayer.TimeMS = ms;

        _lastRequestedPositionSeconds = seconds;
        _suppressPlayerUpdateUntil = DateTime.UtcNow.AddMilliseconds(900);
    }

    private void RefreshFromPlayer()
    {
        var meta = _audioPlayer?.Player?.Media?.Meta(MetadataType.Title);
        string mediaTitle = !string.IsNullOrEmpty(meta) ? meta.Split('.')[0] : "Unknown Title";
        NowPlayingTitle = mediaTitle;

        var lenMS = _audioPlayer.LengthMS;
        var durSec = lenMS > 0 ? lenMS / 1000.0 : 0;

        if (Math.Abs(DurationSeconds - durSec) > 0.5)
        {
            DurationSeconds = durSec;
        }

        var cursec = _audioPlayer.TimeMS / 1000.0;

        if (IsScrubbing)
        {
            CurrentlyText = FormatTime((long)Math.Round(PositionSeconds));
            if (DurationSeconds > 0)
            {
                var remaining = Math.Max(0, DurationSeconds - PositionSeconds);
                DurationText = "-" + FormatTime((long)Math.Round(remaining));
            }
            else
            {
                DurationText = "-0:00";
            }
            return;
        }

        if (DateTime.UtcNow < _suppressPlayerUpdateUntil && _lastRequestedPositionSeconds.HasValue)
        {
            if (Math.Abs(cursec - _lastRequestedPositionSeconds.Value) <= 0.6)
            {
                PositionSeconds = cursec;
                _lastRequestedPositionSeconds = null;
                _suppressPlayerUpdateUntil = DateTime.MinValue;
            }
            else
            {
                PositionSeconds = _lastRequestedPositionSeconds.Value;
            }
        }
        else
        {
            PositionSeconds = cursec;
            _lastRequestedPositionSeconds = null;
        }

        CurrentlyText = FormatTime((long)Math.Round(PositionSeconds));

        if (DurationSeconds > 0)
        {
            var remaining = Math.Max(0, DurationSeconds - PositionSeconds);
            DurationText = "-" + FormatTime((long)Math.Round(remaining));
        }
        else
        {
            DurationText = "-0:00";
        }
    }

    private static string FormatTime(long totalSeconds)
    {
        totalSeconds = Math.Max(0, totalSeconds);
        var ts = TimeSpan.FromSeconds(totalSeconds);

        return ts.TotalHours >= 1
            ? $"{(int)ts.TotalHours}:{ts.Minutes:00}:{ts.Seconds:00}"
            : $"{ts.Minutes}:{ts.Seconds:00}";
    }
    
    [RelayCommand]
    private void IncreaseVolume()
    {
        Volume = Math.Min(100, Volume + 5);
        _audioPlayer.Volume = Volume;
    }

    [RelayCommand]
    private void DecreaseVolume()
    {
        Volume = Math.Max(0, Volume - 5);
        _audioPlayer.Volume = Volume;
    }
    
    [RelayCommand]
    private void MoveForward()
    {
        SeekToSeconds(PositionSeconds + 1);
    }
    
    [RelayCommand]
    private void MoveBackward()
    {
        SeekToSeconds(PositionSeconds - 1);
    }

    public void Dispose()
    {
        _timer.Stop();
        _audioPlayer.Dispose();

        var massage = new Massage("audio player disposed", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }
}
