// C#
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// Class responsible for managing the state and logic of the MediaPlayerWindow, which provides functionality to play audio media files. It handles loading media, controlling playback (play, pause, stop), scrubbing through the media timeline, adjusting volume, and updating the UI with the current playback position and duration.
/// The class also logs significant events related to media playback using an AppLogger instance.
/// </summary>
public partial class MediaPlayerWindowViewModel : ObservableObject, IDisposable
{
    private readonly AppLogger _logger = new();
    [ObservableProperty]
    public AudioPlayer _audioPlayer;
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
    
    private int _currentMediaIndex = 0;
    private List<DownloadedMedia> _mediaList = new();

    /// <summary>
    /// Constructor for the MediaPlayerWindowViewModel, which initializes the view model with an instance of AudioPlayer and a path to the media file to be played.
    /// It sets up a timer to periodically refresh the playback position and duration from the audio player, and it logs significant events such as opening the media file and starting playback.
    /// </summary>
    /// <param name="audioPlayer"></param>
    /// <param name="medias"></param>
    public MediaPlayerWindowViewModel(AudioPlayer audioPlayer, List<DownloadedMedia> medias)
    {
        if (Design.IsDesignMode) return;
        
        _audioPlayer = audioPlayer;
        
        _mediaList = medias;

        _audioPlayer.Volume = volume;

        _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
        _timer.Tick += (s, e) => RefreshFromPlayer();
        _timer.Start();
        
        _audioPlayer.Player.EndReached += OnTrackEnded;
        
        PlayTrack(_currentMediaIndex);
    }
    
    /// <summary>
    /// Plays the media track at the specified index in the media list.
    /// It checks if the index is valid, updates the current media index, opens the media file in the audio player, and starts playback.
    /// It also logs the events of opening the media file and starting playback using the AppLogger instance.
    /// </summary>
    /// <param name="index"></param>
    private void PlayTrack(int index)
    {
        if (index < 0 || index >= _mediaList.Count) return;

        _currentMediaIndex = index;
        _audioPlayer.Open(_mediaList[index].DownloadPath);
        _audioPlayer.Play();

        var massage = new Massage("audio player opened " + Path.GetFileName(_mediaList[index].DownloadPath), DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);

        _audioPlayer.Play();

        massage = new Massage("audio player started playing", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    /// <summary>
    /// Event handler that is called when the currently playing track reaches its end.
    /// It checks if there are more tracks in the media list to play, and if so, it increments the current media index and plays the next track.
    /// If there are no more tracks, it resets the current media index to 0 and stops playback.
    /// </summary>
    /// <param name="sender"></param>
    /// <param name="e"></param>
    private void OnTrackEnded(object? sender, EventArgs e)
    { 
        Dispatcher.UIThread.Post(() =>
        {
            if (_currentMediaIndex + 1 < _mediaList.Count)
            {
                _currentMediaIndex++;
                PlayTrack(_currentMediaIndex);
                RefreshFromPlayer();
            }
            else
            {
                _currentMediaIndex = 0;
                _audioPlayer.Stop();
            }
        });
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Play" button. It starts playback of the currently loaded media in the audio player and logs this event using the AppLogger instance.
    /// This allows the user to control media playback and provides feedback on the action taken.
    /// </summary>
    [RelayCommand] public void Play()
    {
        _audioPlayer.Play();
        var massage = new Massage("audio player started playing", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Pause" button. It pauses playback of the currently loaded media in the audio player and logs this event using the AppLogger instance.
    /// This allows the user to control media playback and provides feedback on the action taken.
    /// </summary>
    [RelayCommand] public void Pause()
    {
        _audioPlayer.Pause();
        var massage = new Massage("audio player paused", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Stop" button. It stops playback of the currently loaded media in the audio player and logs this event using the AppLogger instance.
    /// This allows the user to control media playback and provides feedback on the action taken.
    /// </summary>
    [RelayCommand] public void Stop()
    {
        _audioPlayer.Stop();
        var massage = new Massage("audio player stopped", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }

    /// <summary>
    /// Command method that is executed when the user begins scrubbing through the media timeline (e.g., by dragging a slider).
    /// It sets the IsScrubbing property to true, which can be used to temporarily suspend updates from the audio player while the user is actively scrubbing.
    /// This allows for smoother UI updates and prevents conflicts between user input and automatic updates from the audio player.
    /// </summary>
    [RelayCommand]
    public void BeginScrub()
    {
        IsScrubbing = true;
    }

    /// <summary>
    /// Command method that is executed when the user scrubs to a specific position in the media timeline (e.g., by dragging a slider to a new position). It takes the target position in seconds as a parameter.
    /// The method pauses the audio player, updates the PositionSeconds property to reflect the new position, and updates the CurrentlyText and DurationText properties to show the new playback position and remaining duration.
    /// </summary>
    /// <param name="seconds"></param>
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

    /// <summary>
    /// Command method that is executed when the user finishes scrubbing through the media timeline (e.g., by releasing a slider).
    /// It seeks the audio player to the new position specified by PositionSeconds, sets IsScrubbing to false, and resumes playback.
    /// </summary>
    [RelayCommand]
    public void EndScrub()
    {
        SeekToSeconds(PositionSeconds);
        IsScrubbing = false;
        _audioPlayer.Play();
    }

    /// <summary>
    /// Seeks the audio player to a specific position in the media timeline, given in seconds.
    /// It pauses the audio player, updates the TimeMS property to reflect the new position, and sets a suppression period during which updates from the audio player will be ignored to allow for smoother UI updates.
    /// </summary>
    /// <param name="seconds"></param>
    public void SeekToSeconds(double seconds)
    {
        _audioPlayer.Pause();
        var ms = (long)(Math.Max(0, seconds) * 1000.0);
        _audioPlayer.TimeMS = ms;

        _lastRequestedPositionSeconds = seconds;
        _suppressPlayerUpdateUntil = DateTime.UtcNow.AddMilliseconds(900);
        _audioPlayer.Play();
    }

    /// <summary>
    /// Refreshes the playback position, duration, and media title from the audio player. This method is called periodically by the timer to update the UI with the current state of the audio player.
     /// It checks if the user is currently scrubbing and updates the CurrentlyText and DurationText properties accordingly. If not scrubbing, it updates the PositionSeconds property based on the current time of the audio player and formats the text for display.
     /// The method also handles a suppression period to prevent conflicts between user input and automatic updates from the audio player, ensuring smoother UI updates during scrubbing.
    /// </summary>
    private void RefreshFromPlayer()
    {
        var meta = _audioPlayer.Player.Media?.Meta(MetadataType.Title);
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

    /// <summary>
    /// Formats a given total number of seconds into a string representation of the time in the format "H:MM:SS" if the total hours are 1 or more, or "M:SS" if less than 1 hour.
    /// The method ensures that minutes and seconds are always displayed with two digits for consistency.
    /// </summary>
    /// <param name="totalSeconds"></param>
    /// <returns></returns>
    private static string FormatTime(long totalSeconds)
    {
        totalSeconds = Math.Max(0, totalSeconds);
        var ts = TimeSpan.FromSeconds(totalSeconds);

        return ts.TotalHours >= 1
            ? $"{(int)ts.TotalHours}:{ts.Minutes:00}:{ts.Seconds:00}"
            : $"{ts.Minutes}:{ts.Seconds:00}";
    }
    
    /// <summary>
    /// Increases the volume of the audio player by 5 units, ensuring that the volume does not exceed the maximum limit of 100.
    /// It updates the Volume property and sets the audio player's volume accordingly.
    /// </summary>
    [RelayCommand]
    private void IncreaseVolume()
    {
        Volume = Math.Min(100, Volume + 5);
        _audioPlayer.Volume = Volume;
    }

    /// <summary>
    /// Decreases the volume of the audio player by 5 units, ensuring that the volume does not go below the minimum limit of 0.
    /// It updates the Volume property and sets the audio player's volume accordingly.
    /// </summary>
    [RelayCommand]
    private void DecreaseVolume()
    {
        Volume = Math.Max(0, Volume - 5);
        _audioPlayer.Volume = Volume;
    }
    
    /// <summary>
    /// Moves the playback position forward by 10 seconds.
    /// It calls the SeekToSeconds method with the new target position, which handles pausing, seeking, and resuming playback while ensuring smooth UI updates.
    /// </summary>
    [RelayCommand]
    private void MoveForward()
    {
        SeekToSeconds(PositionSeconds + 10);
    }
    
    /// <summary>
    /// Moves the playback position backward by 10 seconds.
    /// It calls the SeekToSeconds method with the new target position, which handles pausing, seeking, and resuming playback while ensuring smooth UI updates.
    /// The method ensures that the new position does not go below 0 seconds.
    /// </summary>
    [RelayCommand]
    private void MoveBackward()
    {
        SeekToSeconds(PositionSeconds - 10);
    }

    
    /// <summary>
    /// Disposes of the MediaPlayerWindowViewModel by stopping the timer and disposing of the audio player.
    /// It also logs the disposal event using the AppLogger instance.
    /// </summary>
    public void Dispose()
    {
        _timer.Stop();
        _audioPlayer.Dispose();

        var massage = new Massage("audio player disposed", DateTime.Now, "INFO");
        _logger.LogNewMassage(massage);
    }
}
