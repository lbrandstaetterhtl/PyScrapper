using System;
using LibVLCSharp.Shared;

namespace PyScrapperDesktopApp.Models;

public class AudioPlayer : IDisposable
{
    private readonly LibVLC _vlc;
    
    public MediaPlayer Player { get; }
    
    public AudioPlayer()
    {
        Core.Initialize();
        _vlc = new LibVLC();
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
        Player.Dispose();
        _vlc.Dispose();
    }
}