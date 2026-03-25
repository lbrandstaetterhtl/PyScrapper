using System;
using System.Collections.Generic;
using System.Linq;
using LibVLCSharp.Shared;

namespace PyScrapperDesktopApp.Models;

public class AudioPlayer : IDisposable
{
    private readonly LibVLC _libVLC;
    private MediaPlayer _mediaPlayer;
    private readonly List<DownloadedMedia> _playlistTracks = new();
    private readonly List<DownloadedMedia> _originalPlaylistTracks = new();
    private int _currentIndex = -1;

    private bool _disposed;

    public MediaPlayer MediaPlayer => _mediaPlayer;

    private string? CurrentFile {get; set;}

    private bool isShuffleEnabled { get; set; }
    
    public bool HasNext => _currentIndex < _playlistTracks.Count - 1;
    public bool HasPrevious => _currentIndex > 0;
    
    public event EventHandler<string?> TrackChanged;
    
    public event EventHandler<bool> VideoAvailableChanged;
    
    private Media? _currentMedia;

    public AudioPlayer()
    {
        _libVLC = new LibVLC(enableDebugLogs: true, "--verbose=1", "--file-caching=500");
        
        _mediaPlayer = new MediaPlayer(_libVLC);

        _mediaPlayer.EndReached += (s, e) => { PlayNext(); };

        _mediaPlayer.ESAdded += OnEsAdded;
        _mediaPlayer.ESDeleted += OnEsDeleted;
    }
    
    private void OnEsAdded(object? sender, MediaPlayerESAddedEventArgs e)
    {
        if (e.Type == TrackType.Video)
        {
            VideoAvailableChanged?.Invoke(this, true);
        }
    }
    
    private void OnEsDeleted(object? sender, MediaPlayerESDeletedEventArgs e)
    {
        if (e.Type == TrackType.Video)
        {
            VideoAvailableChanged?.Invoke(this, false);
        }
    }
    
    
    public void LoadPlaylist(Playlist playlist)
    {
        var list = AppData.PlayableMedias.Where(m => playlist.MediaIds.Contains(m.Id)).ToList();
        
        _originalPlaylistTracks.Clear();
        _originalPlaylistTracks.AddRange(list);
        
        _playlistTracks.Clear();
        _playlistTracks.AddRange(list);
        _currentIndex = -1;

        if (isShuffleEnabled)
        {
            ShufflePlaylist();
        }
        
        PlayNext();
    }
    
    public void PlayNext()
    {
        if (_playlistTracks.Count == 0) return;
        
        _currentIndex++;
        
        if (_currentIndex >= _playlistTracks.Count) _currentIndex = 0;

        PlayFile(_playlistTracks[_currentIndex].DownloadPath);
    }

    public void PlayPrevious()
    {
        if (_playlistTracks.Count == 0) return;
        
        _currentIndex--;
        
        if (_currentIndex < 0) _currentIndex = _playlistTracks.Count - 1;
        
        PlayFile(_playlistTracks[_currentIndex].DownloadPath);
    }

    public void PlayFile(string filePath)
    {    
        CurrentFile = filePath;

        _mediaPlayer.Stop();

        _currentMedia?.Dispose();

        _currentMedia = new Media(_libVLC, filePath, FromType.FromPath);
        _currentMedia.AddOption(":file-caching=500");

        _mediaPlayer.Play(_currentMedia);

        TrackChanged?.Invoke(this, CurrentFile);
    }

    public void ToggleShuffle()
    {
        isShuffleEnabled = !isShuffleEnabled;
        
        var currentFile = CurrentFile;

        if (isShuffleEnabled)
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
    
    private void ShufflePlaylist()
    {
        var rng = new Random();
        
        for (int i = _playlistTracks.Count - 1; i > 0; i--)
        {
            int j = rng.Next(0, i + 1);
            (_playlistTracks[i], _playlistTracks[j]) = (_playlistTracks[j], _playlistTracks[i]);
        }
    }

    public void Stop()
    {
        _currentIndex = -1;
        _mediaPlayer.Stop();
    }

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
}