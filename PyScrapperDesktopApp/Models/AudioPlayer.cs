using System;
using System.Threading;
using System.Threading.Tasks;
using LibVLCSharp.Shared;

namespace PyScrapperDesktopApp.Models;

public class AudioPlayer : IDisposable
{
    private readonly LibVLC _vlc;
    private bool _disposed;
    private readonly object _disposeLock = new();
    
    public MediaPlayer Player { get; }
    
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
    public void Open(string path)
    {
        using var media = new Media(_vlc, path, FromType.FromPath);
        Player.Media = media;
    }
    

    public void Play()
    {
        Player.Play();
    }
    
    public void Pause()
    {
        Player.Pause();
    }
    
    public void Stop()
    {
        Player.Stop();
    }
    
    public int Volume
    {
        get => Player.Volume;
        set => Player.Volume = Math.Clamp(value, 0, 100);
    }
    
    public long LengthMS => Player.Length;
    
    public long TimeMS
    {
        get => Player.Time;
        set => Player.Time = Math.Max(0, value);
    }
    
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
            // Dispose des nativen LibVLC im Hintergrund, Fehler abfangen
            Task.Run(() =>
            {
                try
                {
                   _vlc.Dispose();
                   Player.Dispose();
                }
                catch
                {
                    // swallow native dispose errors to avoid crash during App shutdown
                }
            });
        }
    }
}