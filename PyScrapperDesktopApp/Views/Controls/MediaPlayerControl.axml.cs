using System;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Threading;
using Avalonia.VisualTree;
using LibVLCSharp.Avalonia;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views.Controls;

public partial class MediaPlayerControl : UserControl
{
    private MediaPlayerControlViewModel _vm;
    private int _playButtonCounter = 0;
    private Playlist? _pendingPlaylist = null;
    private Window? _parentWindow;
    
    public event Action<bool>? OnCompactChanged;

    public MediaPlayerControl()
    {
        InitializeComponent();

        _vm = new MediaPlayerControlViewModel();
        DataContext = _vm;

        SetNavigationButtons();
        SetPlayButton(1);
        SetImageIcons();

        // Wenn aus Compact rausgegangen — VideoView verknüpfen
        _vm.CompactClosed += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                Dispatcher.UIThread.Post(() =>
                {
                    AttachVideoView();
                    ToggleCompactButton.Content = new Image { Source = _vm.ToggleCompactIcon };
                }, DispatcherPriority.Render);
            }, DispatcherPriority.Loaded);
        };

        _vm.CompactOpened += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                VideoView.MediaPlayer = null;
                ToggleCompactButton.Content = new Image { Source = _vm.ToggleCompactIcon };
            }, DispatcherPriority.Loaded);
        };

        // ── SeekSlider ──
        SeekSlider.AddHandler(PointerPressedEvent,
            (s, e) => { if (DataContext is MediaPlayerControlViewModel vm) vm.SeekSliderMoving = true; },
            handledEventsToo: true);

        SeekSlider.AddHandler(PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.SetSeekValue((long)SeekSlider.Value);
                vm.SeekSliderMoving = false;
            },
            handledEventsToo: true);

        SeekSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is MediaPlayerControlViewModel vm && vm.SeekSliderMoving)
                vm.PositionSeconds = e.NewValue;
        };

        // ── VolumeSlider ──
        VolumeSlider.AddHandler(PointerPressedEvent,
            (s, e) => { if (DataContext is MediaPlayerControlViewModel vm) vm.VolumeSliderMoving = true; },
            handledEventsToo: true);

        VolumeSlider.AddHandler(PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.SetVolume((int)VolumeSlider.Value);
                vm.VolumeSliderMoving = false;
            },
            handledEventsToo: true);

        VolumeSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is MediaPlayerControlViewModel vm && vm.VolumeSliderMoving)
                vm.Volume = (int)e.NewValue;
        };

        // ── Play Buttons ──
        CompactPlayButton.Click += PlayButtonClick;
        PlayButton.Click        += PlayButtonClick;

        // ── Theme Change ──
        App.Current.ActualThemeVariantChanged += (s, e) =>
        {
            int counter = _playButtonCounter == 0 ? 1 : 0;
            SetNavigationButtons();
            SetPlayButton(counter);
            SetImageIcons();
        };

        _vm.CompactClosed += (s, e) =>
        {
            OnCompactChanged?.Invoke(false);
            VideoView.MinHeight = 300;
        };
        _vm.CompactOpened += (s, e) => OnCompactChanged?.Invoke(true);
        
        VideoView.LayoutUpdated += (s, e) =>
        {
            if (_vm.AspectRatio <= 0) return;
    
            double availableWidth = VideoView.Parent is Control parent
                ? parent.Bounds.Width
                : VideoView.Bounds.Width;

            if (availableWidth <= 0) return;

            _vm.VideoWidth  = availableWidth;
            _vm.VideoHeight = availableWidth / _vm.AspectRatio;
        };
    }

    private void PlayButtonClick(object? sender, RoutedEventArgs e)
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
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
    }

    /// <summary>
    /// Lädt eine neue Playlist und startet die Wiedergabe.
    /// </summary>
    public void LoadAndPlay(Playlist playlist)
    {
        _pendingPlaylist = playlist;

        Dispatcher.UIThread.Post(() =>
        {
            AttachVideoView();
        }, DispatcherPriority.Loaded);

        Task.Delay(2000).Wait();
    }

    /// <summary>
    /// Verknüpft den VideoView mit dem MediaPlayer.
    /// Wird aufgerufen nachdem der Normal-View sichtbar ist.
    /// </summary>
    private void AttachVideoView()
    {
        if (_pendingPlaylist != null)
        {
            VideoView.MediaPlayer = null;
            _vm.VideoViewLoaded(_pendingPlaylist);
            _pendingPlaylist = null;
        }

        // Warten bis VideoView wirklich im Visual Tree ist
        if (VideoView.IsAttachedToVisualTree())
        {
            VideoView.MediaPlayer = _vm.MediaPlayer;
        }
        else
        {
            void OnAttached(object? sender, VisualTreeAttachmentEventArgs e)
            {
                VideoView.MediaPlayer = _vm.MediaPlayer;
                VideoView.AttachedToVisualTree -= OnAttached;
            }
            VideoView.AttachedToVisualTree += OnAttached;
        }
    }

    /// <summary>
    /// Gibt LibVLC-Ressourcen frei.
    /// </summary>
    public void Dispose() => _vm?.Dispose();

    private void SetPlayButton(int counter)
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        var bitmap = counter == 0 ? vm.PlayIcon : vm.PauseIcon;
        CompactPlayButton.Content = new Image { Source = bitmap };
        PlayButton.Content        = new Image { Source = bitmap };
    }

    private void SetNavigationButtons()
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        PreviousButton.Content        = new Image { Source = vm.BackIcon };
        NextButton.Content            = new Image { Source = vm.ForwardIcon };
        CompactPreviousButton.Content = new Image { Source = vm.BackIcon };
        CompactNextButton.Content     = new Image { Source = vm.ForwardIcon };
        ShuffleCheckbox.Content       = new Image { Source = vm.ShuffleIcon };
        ToggleCompactButton.Content   = new Image { Source = vm.ToggleCompactIcon };
    }

    private void SetImageIcons()
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        SongIcon.Source   = vm.SongIcon;
        VolumeIcon.Source = vm.VolumeIcon;
    }
}