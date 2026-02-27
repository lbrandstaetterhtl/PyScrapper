using System;
using System.IO;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MediaPlayerWindowViewModel : ObservableObject
{
    private readonly AudioPlayer _audioPlayer;
    private readonly DispatcherTimer _timer;
    
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
        
        _timer = new DispatcherTimer {Interval = TimeSpan.FromMilliseconds(200)};
        _timer.Tick += (s, e) => RefreshFromPlayer();
        _timer.Start();
        
        _audioPlayer.Open(path);
        _audioPlayer.Play();
    }
    [RelayCommand] public void Play() => _audioPlayer.Play();
    [RelayCommand] public void Pause() => _audioPlayer.Pause();
    [RelayCommand] public void Stop() => _audioPlayer.Stop();
    
    public void SeekToSeconds(long seconds)
    {
        _audioPlayer.TimeMS = seconds * 1000;
    }
    
    private void  RefreshFromPlayer()
    {
        var lenMS = _audioPlayer.LengthMS;
        var durSec = lenMS > 0 ? lenMS / 1000.0 : 0;
        
        if (Math.Abs(durationSeconds - durSec) > 0.5)
        {
            durationSeconds = durSec;
        }
        
        var cursec = _audioPlayer.TimeMS / 1000.0;
        
        if (!isScrubbing)
        {
            positionSeconds = cursec;
        }
        
        var displaySec = isScrubbing ? positionSeconds : cursec;
        
        currentlyText = FormatTime((long)Math.Round(displaySec));

        if (durationSeconds > 0)
        {
            var remaining = Math.Max(0, durationSeconds - displaySec);
            
            durationText = "-" + FormatTime((long)Math.Round(remaining));
        }
        else
        {
            durationText = "-0:00";
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
    
    public void Dispose()
    {
        _timer.Stop();
        _audioPlayer.Dispose();
    }
}