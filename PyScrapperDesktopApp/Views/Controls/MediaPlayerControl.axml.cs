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

    /// <summary>
    /// Event das MainWindow abonniert um auf Fullscreen-Änderungen zu reagieren.
    /// </summary>
    public event Action<bool>? OnFullscreenChanged;

    public MediaPlayerControl()
    {
        InitializeComponent();

        _vm = new MediaPlayerControlViewModel();
        DataContext = _vm;

        SetNavigationButtons();
        SetPlayButton(1);
        SetImageIcons();

        // ── Fullscreen-Event ──
        _vm.FullscreenChanged += (s, isFullscreen) =>
        {
            OnFullscreenChanged?.Invoke(isFullscreen);

            Dispatcher.UIThread.Post(() =>
            {
                AttachVideoViews(); // zentral — nicht doppelt implementieren
            }, DispatcherPriority.Loaded);
        };

        // ── CompactClosed-Event: VideoView ist jetzt sichtbar ──
        _vm.CompactClosed += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                Dispatcher.UIThread.Post(() =>
                {
                    AttachVideoViews();
                }, DispatcherPriority.Render);
            }, DispatcherPriority.Loaded);
        };

        // ── SeekSlider (Normal View) ──
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

        // ── VolumeSlider (Normal View) ──
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

        // ── Play Buttons (alle drei Views) ──
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
    /// Wenn der Player gerade kompakt ist, wird die Playlist gespeichert
    /// und erst beim Öffnen des normalen Views verknüpft.
    /// </summary>
    public void LoadAndPlay(Playlist playlist)
    {
        _pendingPlaylist = playlist;

        Dispatcher.UIThread.Post(() =>
        {
            AttachVideoViews();
        }, DispatcherPriority.Loaded);

        Task.Delay(2000).Wait();
    }

    /// <summary>
    /// Verknüpft den MediaPlayer mit dem richtigen VideoView
    /// je nach aktuellem Mode (Normal / Fullscreen).
    /// Wird aufgerufen nachdem der VideoView sichtbar wurde.
    /// </summary>
    private VideoView? _videoView;

    private void AttachVideoViews()
    {
        if (_pendingPlaylist != null)
        {
            if (_videoView != null) _videoView.MediaPlayer = null;
            _vm.VideoViewLoaded(_pendingPlaylist);
            _pendingPlaylist = null;
        }

        _videoView ??= new VideoView();

        if (_vm.IsCompact)
        {
            VideoViewHost.Content = null;
            VideoViewCompactHost.Content = _videoView;
            _videoView.MediaPlayer = _vm.MediaPlayer;
        }
        else
        {
            VideoViewCompactHost.Content = null;
            VideoViewHost.Content = _videoView;

            // Warten bis VideoView wirklich im Visual Tree ist
            if (_videoView.IsAttachedToVisualTree())
            {
                _videoView.MediaPlayer = _vm.MediaPlayer;
            }
            else
            {
                void OnAttached(object? sender, VisualTreeAttachmentEventArgs e)
                {
                    _videoView.MediaPlayer = _vm.MediaPlayer;
                    _videoView.AttachedToVisualTree -= OnAttached;
                }
                _videoView.AttachedToVisualTree += OnAttached;
            }
        }
    }
    
    /// <summary>
    /// Gibt LibVLC-Ressourcen frei. Beim Schließen des MainWindow aufrufen.
    /// </summary>
    public void Dispose() => _vm?.Dispose();

    private void SetPlayButton(int counter)
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        var bitmap = counter == 0 ? vm.PlayIcon : vm.PauseIcon;
    
        // Jeder Button bekommt sein eigenes neues Image-Objekt
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
    }

    private void SetImageIcons()
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        SongIcon.Source = vm.SongIcon;
        VolumeIcon.Source = vm.VolumeIcon;
    }
}