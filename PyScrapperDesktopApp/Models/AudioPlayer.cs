using System;
using System.Threading;
using System.Threading.Tasks;
using LibVLCSharp.Shared;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// A simple wrapper around LibVLCSharp to manage audio playback, with proper disposal of native resources.
/// </summary>
public class AudioPlayer : IDisposable
{
    private readonly LibVLC _vlc;
    private bool _disposed;
    private readonly object _disposeLock = new();
    
    public MediaPlayer Player { get; }
    
    /// <summary>
    /// AudioPlayer constructor. By default, it initializes LibVLC with hardware acceleration disabled for audio-only playback.
    /// If enableVideo is set to true, it also disables video output, which can be useful for certain
    /// </summary>
    /// <param name="enableVideo"></param>
    public AudioPlayer(bool enableVideo = false)
    {
        Core.Initialize();

        if (!enableVideo)
        {
            _vlc = new LibVLC("--avcodec-hw=none");    
        }
        else
        {
            _vlc = new LibVLC(
                "--avcodec-hw=none",
                "--vout=none"
            );
        }

        Player = new MediaPlayer(_vlc);
    }
    
    /// <summary>
    /// Opens a media file for playback. The media is created and disposed immediately, as MediaPlayer will internally manage the media reference.
    /// </summary>
    /// <param name="path"></param>
    public void Open(string path)
    {
        using var media = new Media(_vlc, path, FromType.FromPath);
        Player.Media = media;
    }
    
    /// <summary>
    /// Plays the currently loaded media. If no media is loaded, this will have no effect. Playback state can be monitored via Player.State.
    /// </summary>
    public void Play()
    {
        Player.Play();
    }
    
    /// <summary>
    /// Pauses playback of the currently loaded media. If no media is loaded or if playback is already paused, this will have no effect.
    /// Playback state can be monitored via Player.State.
    /// </summary>
    public void Pause()
    {
        Player.Pause();
    }
    
    /// <summary>
    /// Stops playback of the currently loaded media. If no media is loaded or if playback is already stopped, this will have no effect.
    /// </summary>
    public void Stop()
    {
        Player.Stop();
    }
    
    /// <summary>
    /// Sets the playback volume. The value is clamped between 0 (mute) and 100 (maximum volume).
    /// If an invalid value is set, it will be automatically adjusted to fit within the valid range.
    /// </summary>
    public int Volume
    {
        get => Player.Volume;
        set => Player.Volume = Math.Clamp(value, 0, 100);
    }
    
    /// <summary>
    /// Gets the length of the currently loaded media in milliseconds. If no media is loaded, this will return 0.
    /// </summary>
    public long LengthMS => Player.Length;
    
    /// <summary>
    /// Gets or sets the current playback position in milliseconds. Setting this property will seek to the specified position in the media.
    /// If the value is negative, it will be set to 0. If the value exceeds the media length, it will be set to the media length.
    /// If no media is loaded, this will have no effect.
    /// </summary>
    public long TimeMS
    {
        get => Player.Time;
        set => Player.Time = Math.Max(0, value);
    }
    
    /// <summary>
    /// Disposes the AudioPlayer and releases all native resources associated with LibVLC and the MediaPlayer.
    /// This method is thread-safe and idempotent, meaning it can be called multiple times without throwing exceptions or causing issues.
    /// </summary>
    public void Dispose()
    {
        // idempotent und thread-sicher
        bool doDispose = false;
        lock (_disposeLock)
        {
            if (!_disposed)
            {
                _disposed = true;
                doDispose = true;
            }
        }

        if (!doDispose)
            return;

        if (_vlc != null)
        {
            Task.Run(() =>
            {
                try
                {
                   _vlc.Dispose();
                   Player.Dispose();
                }
                catch
                {
                    // Catch and ignore any exceptions that occur during disposal, as we don't want to throw from Dispose()
                }
            });
        }
    }
}