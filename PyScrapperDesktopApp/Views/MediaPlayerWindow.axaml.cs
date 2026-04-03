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
    public MediaPlayerWindow(Playlist playlist = null)
    {
        
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new MediaPlayerWindowViewModel(playlist: playlist);
        DataContext = vm;
        
        SetNavigationButtons();
        SetPlayButton(1);
        SetImageIcons();
        
        Opened += (s, e) =>
        {
            if (DataContext is not MediaPlayerWindowViewModel vm) return;

            VideoView.MediaPlayer = vm.MediaPlayer;
            
            vm.VideoViewLoaded();
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
                vm.SetSeekValue((long)SeekSlider.Value);
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
                vm.SetVolume((int)VolumeSlider.Value);
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
                SetPlayButton(_playButtonCounter);
                _playButtonCounter++;
            }
            else
            {
                vm.Play();
                SetPlayButton(_playButtonCounter);
                _playButtonCounter--;
            }
        };
        
        App.Current.ActualThemeVariantChanged += (s, e) =>
        {
            int counter = _playButtonCounter == 0 ? 1 : 0;
            SetNavigationButtons();
            SetPlayButton(counter);
            SetImageIcons();
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
    
    private void SetNavigationButtons()
    {
        if (DataContext is not MediaPlayerWindowViewModel vm) return;
        PreviousButton.Content = vm.BackIcon;
        NextButton.Content = vm.ForwardIcon;
        ShuffleCheckbox.Content = vm.ShuffleIcon;
    }

    private void SetPlayButton(int counter)
    {
        if (DataContext is not MediaPlayerWindowViewModel vm) return;
        if (counter == 0)
            PlayButton.Content = vm.PlayIcon;
        else
            PlayButton.Content = vm.PauseIcon;
    }

    private void SetImageIcons()
    {
        if (DataContext is not MediaPlayerWindowViewModel vm) return;
        SongIcon.Source = vm.SongIcon;
        VolumeIcon.Source = vm.VolumeIcon;
    }
}