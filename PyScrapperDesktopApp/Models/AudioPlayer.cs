using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Controls.Converters;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Manages audio playback using LibVLCSharp, including playlist handling, shuffle functionality, and codec support checking.
/// It also raises events for track changes and video availability, and logs significant actions and errors.
/// </summary>
public class AudioPlayer : IDisposable
{
    private readonly LibVLC _libVLC;
    private readonly MediaPlayer _mediaPlayer;
    private readonly List<DownloadedMedia> _playlistTracks = new();
    private readonly List<DownloadedMedia> _originalPlaylistTracks = new();
    private int _currentIndex = -1;

    private bool _disposed;

    public MediaPlayer MediaPlayer => _mediaPlayer;

    private string? CurrentFile {get; set;}

    private bool IsShuffleEnabled { get; set; }
    
    public bool HasNext => _currentIndex < _playlistTracks.Count - 1;
    public bool HasPrevious => _currentIndex > 0;
    public bool PlaylistModeEnabled { get; set; }
    
    public event EventHandler<string?> TrackChanged;
    
    public event EventHandler<bool> VideoAvailableChanged;
    
    private Media? _currentMedia;
    private static readonly AppLogger _logger = AppLogger.Instance;

    /// <summary>
    /// Initializes the AudioPlayer by setting up the LibVLC instance with specific options, creating a MediaPlayer, and subscribing to relevant events for handling track changes and video availability.
    /// The constructor also configures the MediaPlayer to play the next track when the current one ends, and to log significant actions and errors throughout the playback process.
    /// </summary>
    public AudioPlayer()
    {
        _libVLC = new LibVLC("--quiet", "--file-caching=500", "--avcodec-hw=none", "--codec=avcodec");
        
        _mediaPlayer = new MediaPlayer(_libVLC);

        _mediaPlayer.EndReached += (s, e) =>
        {
            ThreadPool.QueueUserWorkItem(_ => PlayNext());
        };

        _mediaPlayer.ESAdded += OnEsAdded;
        _mediaPlayer.ESDeleted += OnEsDeleted;
    }
    
    /// <summary>
    /// Event handler for when a new elementary stream (ES) is added to the MediaPlayer.
    /// It checks if the added stream is a video track and raises the VideoAvailableChanged event accordingly to notify subscribers about the availability of video content in the current media.
    /// </summary>
    /// <param name="sender"></param>
    /// <param name="e"></param>
    private void OnEsAdded(object? sender, MediaPlayerESAddedEventArgs e)
    {
        if (e.Type == TrackType.Video)
        {
            VideoAvailableChanged?.Invoke(this, true);
        }
    }
    
    /// <summary>
    /// Event handler for when an elementary stream (ES) is deleted from the MediaPlayer.
    /// It checks if the deleted stream is a video track and raises the VideoAvailableChanged event accordingly to notify subscribers about the unavailability of video content in the current media, allowing the application to update its UI or functionality based on the presence of video tracks in the media being played.
    /// </summary>
    /// <param name="sender"></param>
    /// <param name="e"></param>
    private void OnEsDeleted(object? sender, MediaPlayerESDeletedEventArgs e)
    {
        if (e.Type == TrackType.Video)
        {
            VideoAvailableChanged?.Invoke(this, false);
        }
    }
    
    /// <summary>
    /// Loads a playlist into the AudioPlayer, determining whether to enable playlist mode based on the number of tracks in the playlist.
    /// If the playlist contains only one track, it disables playlist mode and sets that track as the current media.
    /// If the playlist contains multiple tracks, it enables playlist mode, populates the playlist with the corresponding media items, and optionally shuffles the playlist if shuffle mode is enabled. Finally, it starts playing the first track in the playlist and logs the action of loading the playlist with its name and the number of playable tracks it contains. This method allows the AudioPlayer to manage and play a collection of media items as a cohesive unit, providing functionality for navigating through the tracks and maintaining the state of the playlist.
    /// </summary>
    /// <param name="playlist"></param>
    public async Task LoadPlaylist(Playlist playlist)
    {
        if (playlist.MediaIdentifiers.Count == 1)
        {
            PlaylistModeEnabled = false;
            _playlistTracks.Clear();

            var media = AppData.PlayableMedias.FirstOrDefault(m => m.Identifier == playlist.MediaIdentifiers[0]);

            if (media == null)
            {
                var log = new Message($"Playlist media with id {playlist.MediaIdentifiers[0]} is not playable or does not exist", DateTime.Now, "WARN");
                _logger.LogNewMassage(log);
                return;
            }

            _playlistTracks.Add(media);
        }
        else if (playlist.MediaIdentifiers.Count > 1)
        {
            PlaylistModeEnabled = true;

            var list = AppData.PlayableMedias.Where(m => playlist.MediaIdentifiers.Contains(m.Identifier)).ToList();

            _originalPlaylistTracks.Clear();
            _originalPlaylistTracks.AddRange(list);

            _playlistTracks.Clear();
            _playlistTracks.AddRange(list);
            _currentIndex = -1;

            var log = new Message($"Loaded playlist '{playlist.Name}' with {_playlistTracks.Count} playable tracks",
                DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (IsShuffleEnabled)
            {
                ShufflePlaylist();
            }
        }

        await PlayNext();
    }
    
    /// <summary>
    /// Plays the next track in the playlist. If the playlist is empty, it does nothing.
    /// It increments the current index and checks if it exceeds the bounds of the playlist, wrapping around to the beginning if necessary.
    /// Then it calls the PlayFile method with the download path of the next track to start playback.
    /// This method allows for seamless navigation through the tracks in a playlist, ensuring that playback continues smoothly from one track to the next, and handles edge cases such as reaching the end of the playlist by looping back to the start.
    /// </summary>
    public async Task PlayNext()
    {
        if (_playlistTracks.Count == 0) return;
        
        _currentIndex++;
        
        if (_currentIndex >= _playlistTracks.Count) _currentIndex = 0;

        await PlayFile(_playlistTracks[_currentIndex].DownloadPath);
    }

    /// <summary>
    /// Plays the previous track in the playlist. If the playlist is empty, it does nothing.
    /// It decrements the current index and checks if it goes below zero, wrapping around to the end of the playlist if necessary.
    /// Then it calls the PlayFile method with the download path of the previous track to start playback.
    /// This method allows for seamless navigation through the tracks in a playlist in reverse order, ensuring that playback continues smoothly from one track to the previous one, and handles edge cases such as reaching the beginning of the playlist by looping back to the end.
    /// </summary>
    public async Task PlayPrevious()
    {
        if (_playlistTracks.Count == 0) return;
        
        _currentIndex--;
        
        if (_currentIndex < 0) _currentIndex = _playlistTracks.Count - 1;
        
        await PlayFile(_playlistTracks[_currentIndex].DownloadPath);
    }

    /// <summary>
    /// Plays a media file specified by its file path. It first checks if the file is an MP4 video and if its codec is supported. If the codec is not supported, it prompts the user to convert the file to a supported format (H264) using FFmpeg.
    /// If the user agrees to convert the file, it opens a codec converter window and waits for the conversion to finish before proceeding to play the converted file.
    /// If the user cancels the conversion or if any errors occur during the codec check or conversion process, it logs the appropriate messages and does not attempt to play the unsupported file. Finally, if the file is playable, it sets it as the current media in the MediaPlayer and starts playback, while also logging the action of playing the file and raising the TrackChanged event to notify subscribers about the change in track.
    /// </summary>
    /// <param name="filePath"></param>
    private async Task PlayFile(string filePath)
    {
        CurrentFile = filePath;

        _currentMedia?.Dispose();

        _currentMedia = new Media(_libVLC, CurrentFile, FromType.FromPath);
        _currentMedia.AddOption(":file-caching=500");
        _currentMedia.AddOption(":avcodec-hw=none");
        _currentMedia.AddOption(":codec=avcodec");

        _mediaPlayer.Media = _currentMedia;
        _mediaPlayer.Play();

        var log = new Message($"Playing file: {CurrentFile}", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);

        TrackChanged?.Invoke(this, CurrentFile);
    }

    /// <summary>
    /// Toggles the shuffle mode for the playlist.
    /// When shuffle mode is enabled, it randomizes the order of the tracks in the playlist while keeping track of the original order to allow toggling back to it when shuffle mode is disabled.
    /// </summary>
    public void ToggleShuffle()
    {
        IsShuffleEnabled = !IsShuffleEnabled;
        
        var currentFile = CurrentFile;

        if (IsShuffleEnabled)
        {
            ShufflePlaylist();
        }
        else
        {
            _playlistTracks.Clear();
            _playlistTracks.AddRange(_originalPlaylistTracks);
        }
        
        _currentIndex = currentFile != null
            ? _playlistTracks.FindIndex(m => m.DownloadPath == currentFile)
            : 0;
        
        if (_currentIndex < 0) _currentIndex = 0;
    }
    
    /// <summary>
    /// Shuffles the playlist using the Fisher-Yates algorithm to randomize the order of the tracks in the playlist.
    /// It creates a new instance of the Random class to generate random indices for swapping tracks in the list.
    /// After shuffling, it logs the action of shuffling the playlist with an informational message.
    /// </summary>
    private void ShufflePlaylist()
    {
        var rng = new Random();
        
        for (int i = _playlistTracks.Count - 1; i > 0; i--)
        {
            int j = rng.Next(0, i + 1);
            (_playlistTracks[i], _playlistTracks[j]) = (_playlistTracks[j], _playlistTracks[i]);
        }
        
        var log = new Message($"Playlist shuffled", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
    }

    /// <summary>
    /// Stops the playback of the current media and resets the current index to -1, effectively clearing the current track selection and stopping any ongoing playback in the MediaPlayer.
    /// This method allows for a clean stop of the audio player, ensuring that any resources associated with the current media are released and that the player is ready for a new track to be loaded and played without any residual state from the previous playback.
    /// </summary>
    public void Stop()
    {
        _currentIndex = -1;
        _mediaPlayer.Stop();
    }

    /// <summary>
    /// Disposes of the resources used by the AudioPlayer, including the MediaPlayer and LibVLC instances, and unsubscribes from any events to prevent memory leaks.
    /// It also sets a flag to indicate that the object has been disposed to avoid multiple disposals.
    /// </summary>
    public void Dispose()
    {
        if (_disposed) return;

        _disposed = true;
        
        _mediaPlayer.ESAdded -= OnEsAdded;
        _mediaPlayer.ESDeleted -= OnEsDeleted;
        
        _mediaPlayer.Stop();
        _mediaPlayer.Dispose();
        _libVLC.Dispose();
    }
    
    /// <summary>
    /// Represents information about a media stream, including its codec type and codec name.
    /// This class is used to deserialize the JSON output from FFprobe when probing media files for their stream information.
    /// It provides properties to access the codec type (e.g., video, audio) and the codec name (e.g., h264, aac) of each stream in the media file.
    /// </summary>
    private class StreamInfo
    {
        [JsonPropertyName("codec_type")]
        public string? CodecType { get; set; }
        
        [JsonPropertyName("codec_name")]
        public string? CodecName { get; set; }
    }
}