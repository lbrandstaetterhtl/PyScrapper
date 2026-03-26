using System;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaPlayerWindow : Window
{
    private int _playButtonCounter = 0;
    public MediaPlayerWindow(DownloadedMedia media = null, Playlist playlist = null)
    {
        
        InitializeComponent();
        
        var vm = new MediaPlayerWindowViewModel();
        DataContext = vm;
        
        Opened += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;

            VideoView.MediaPlayer = vm.MediaPlayer;

            if (playlist != null)
            {
                vm.LoadPlaylist(playlist);
                vm.IsPlaylistMode = true;
            }
            else if (media != null)
            {
                vm._audioPlayer.PlayFile(media.DownloadPath);
                vm.IsPlaylistMode = false;
            }
        };

        Closing += OnWindowClosing;
        CloseButton.Click += (s, e) => Close();
        
        SeekSlider.AddHandler(
            PointerPressedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerWindowViewModel vm) return;
                vm.SeekSliderMoving = true;
            },
            handledEventsToo: true
        );

        SeekSlider.AddHandler(
            PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerWindowViewModel vm) return;
                vm._audioPlayer.MediaPlayer.Time = (long)(SeekSlider.Value * 1000);
                vm.SeekSliderMoving = false;
            },
            handledEventsToo: true
        );

        SeekSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;
            if (vm.SeekSliderMoving)
                vm.PositionSeconds = e.NewValue;
        };
        
        VolumeSlider.AddHandler(
            PointerPressedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerWindowViewModel vm) return;
                vm.VolumeSliderMoving = true;
            },
            handledEventsToo: true
        );

        VolumeSlider.AddHandler(
            PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerWindowViewModel vm) return;
                vm._audioPlayer.MediaPlayer.Volume = (int)VolumeSlider.Value;
                vm.VolumeSliderMoving = false;
            },
            handledEventsToo: true
        );

        VolumeSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;
            if (vm.VolumeSliderMoving)
                vm.Volume = (int)e.NewValue;
        };
        
        PlayButton.Click += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;
            if (_playButtonCounter == 0)
            {
                vm.Pause();
                PlayButton.Content = "Play";
                _playButtonCounter++;
            }
            else
            {
                vm.Play();
                PlayButton.Content = "Pause";
                _playButtonCounter--;
            }
        };
        
        StopButton.Click += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;
            vm.Pause();
            PlayButton.Content = "Play";
            _playButtonCounter = 1;
        };
    }
    
    private void OnWindowClosing(object? sender, WindowClosingEventArgs e)
    {
        if (DataContext is MediaPlayerWindowViewModel vm)
        {
            vm.MediaPlayer.Stop();
        }
        
        VideoView.MediaPlayer = null;

        if (DataContext is IDisposable disposable)
        {
            disposable.Dispose();
        }
    }
}