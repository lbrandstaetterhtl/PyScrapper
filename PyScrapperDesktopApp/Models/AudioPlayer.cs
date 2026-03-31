using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Controls.Converters;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;

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

    private bool IsShuffleEnabled { get; set; }
    
    public bool HasNext => _currentIndex < _playlistTracks.Count - 1;
    public bool HasPrevious => _currentIndex > 0;
    public bool PlaylistModeEnabled { get; set; }
    
    public event EventHandler<string?> TrackChanged;
    
    public event EventHandler<bool> VideoAvailableChanged;
    
    private Media? _currentMedia;
    private static readonly AppLogger _logger = new();

    public AudioPlayer(MediaPlayerWindowViewModel vm)
    {
        _libVLC = new LibVLC("--verbose=1", "--file-caching=500", "--avcodec-hw=none", "--codec=avcodec");
        
        _mediaPlayer = new MediaPlayer(_libVLC);

        _mediaPlayer.EndReached += (s, e) =>
        {
            if (PlaylistModeEnabled)
            {
                System.Threading.ThreadPool.QueueUserWorkItem(_ => PlayNext());
            }
            else
            {
                vm.SetToBeginning();
            }
        };

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
        
        var log = new Massage($"Loaded playlist '{playlist.Name}' with {_playlistTracks.Count} playable tracks", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);

        if (IsShuffleEnabled)
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

    public async Task PlayFile(string filePath)
    {
        bool isSupported = true;
        if (filePath.EndsWith(".mp4"))
        {
            isSupported = await IsSupportedCodec(filePath);
        }

        if (!isSupported)
        {
            var media = AppData.DownloadedMedias.FirstOrDefault(m => m.DownloadPath == filePath);
            
            if (media != null)
                media.IsPlayable = false;
            
            
            if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop) return;
            
            string message = $"The video codec for the file '{filePath}' is not supported. Would you like to convert the file to the supported format H264.";
            var confirmationWindow = new ConfirmationWindow(message);
            var result = await confirmationWindow.ShowDialog<bool>(desktop.MainWindow);

            if (!result)
                return;
            
            string outputPath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(filePath) ?? "", System.IO.Path.GetFileNameWithoutExtension(filePath) + "_converted.mp4");
            
            var converterWindow = new CodecConverterWindow(inputPath: filePath, outputPath: outputPath);
            bool finished = await converterWindow.ShowDialog<bool>(desktop.MainWindow);

            if (!finished)
            {
                var logg = new Massage($"User canceled the codec conversion for file '{filePath}'", DateTime.Now, "INFO");
                _logger.LogNewMassage(logg);
                return;
            }
            else
            {
                filePath = outputPath;
            }
        }
        
        CurrentFile = filePath;

        _currentMedia?.Dispose();

        _currentMedia = new Media(_libVLC, CurrentFile, FromType.FromPath);
        _currentMedia.AddOption(":file-caching=500");
        _currentMedia.AddOption(":avcodec-hw=none");
        _currentMedia.AddOption(":codec=avcodec");

        _mediaPlayer.Media = _currentMedia;
        _mediaPlayer.Play();
        
        var log = new Massage($"Playing file: {CurrentFile}", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);

        TrackChanged?.Invoke(this, CurrentFile);
    }

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
    
    private void ShufflePlaylist()
    {
        var rng = new Random();
        
        for (int i = _playlistTracks.Count - 1; i > 0; i--)
        {
            int j = rng.Next(0, i + 1);
            (_playlistTracks[i], _playlistTracks[j]) = (_playlistTracks[j], _playlistTracks[i]);
        }
        
        var log = new Massage($"Playlist shuffled", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
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

    public static async Task<bool> IsSupportedCodec(string path)
    {
        var codec = await GetVideoCodec(path);
        codec = codec.Trim();
        
        if (string.IsNullOrEmpty(codec))
        {
            return false;
        }
        else
        {
            var supportedCodecs = new[] { "h264"};
            return supportedCodecs.Contains(codec);
        }
    }

    private static async Task<string?> GetVideoCodec(string path)
    {
        var process = new Process();

        process.StartInfo = new ProcessStartInfo
        {
            FileName = "ffprobe",
            Arguments = $"-v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 \"{path}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        
        process.Start();
        
        string output = await process.StandardOutput.ReadToEndAsync();
        string error = await process.StandardError.ReadToEndAsync() ?? "";
        
        await process.WaitForExitAsync();

        if (!string.IsNullOrWhiteSpace(error))
        {
            var log = new Massage($"Error checking codec for file '{path}': {error}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
                return "";
            
            var messageBox = new MessageBox($"An error occurred while checking the video codec for the file '{path}': {error}");
            await messageBox.ShowDialog(desktop.MainWindow);
            return "";
        }
        else
        {
            return output;
        }
    }
}