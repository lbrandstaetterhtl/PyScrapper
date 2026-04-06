using Avalonia.Controls;
using Avalonia.Interactivity;
using LibVLCSharp.Avalonia;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views.Controls;

public partial class MediaPlayerControl : UserControl
{
    private MediaPlayerControlViewModel _vm;
    private int _playButtonCounter = 0;
    public MediaPlayerControl()
    {
        InitializeComponent();
        
        _vm = new MediaPlayerControlViewModel();
        DataContext = _vm;
        
        SetupVideoView();
        SetNavigationButtons();
        SetPlayButton(1);
        SetImageIcons();
        
        SeekSlider.AddHandler(
            PointerPressedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.SeekSliderMoving = true;
            },
            handledEventsToo: true
        );

        SeekSlider.AddHandler(
            PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.SetSeekValue((long)SeekSlider.Value);
                vm.SeekSliderMoving = false;
            },
            handledEventsToo: true
        );

        SeekSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is not MediaPlayerControlViewModel vm) return;
            if (vm.SeekSliderMoving)
                vm.PositionSeconds = e.NewValue;
        };
        
        VolumeSlider.AddHandler(
            PointerPressedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.VolumeSliderMoving = true;
            },
            handledEventsToo: true
        );

        VolumeSlider.AddHandler(
            PointerReleasedEvent,
            (s, e) =>
            {
                if (DataContext is not MediaPlayerControlViewModel vm) return;
                vm.SetVolume((int)VolumeSlider.Value);
                vm.VolumeSliderMoving = false;
            },
            handledEventsToo: true
        );

        VolumeSlider.ValueChanged += (s, e) =>
        {
            if (DataContext is not MediaPlayerControlViewModel vm) return;
            if (vm.VolumeSliderMoving)
                vm.Volume = (int)e.NewValue;
        };
        
        PlayButton.Click += (s, e) =>
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
        };
        
        App.Current.ActualThemeVariantChanged += (s, e) =>
        {
            int counter = _playButtonCounter == 0 ? 1 : 0;
            SetNavigationButtons();
            SetPlayButton(counter);
            SetImageIcons();
        };;
    }
    
    /// <summary>
    /// Loads a new playlist into the existing player and starts playback.
    /// Called whenever the user double-clicks a media item or playlist.
    /// </summary>
    /// <param name="playlist"></param>
    public void LoadAndPlay(Playlist playlist)
    {
        _vm.LoadPlaylist(playlist);
        SetupVideoView();
    }

    /// <summary>
    /// Disposes the ViewModel and releases LibVLC resources.
    /// Call this when the MainWindow is closing.
    /// </summary>
    public void Dispose() => _vm?.Dispose();


    private void SetupVideoView()
    {
        var videoView = this.FindControl<VideoView>("VideoView");
        if (videoView == null || _vm == null) return;

        videoView.Loaded += (_, _) =>
        {
            videoView.MediaPlayer = _vm.MediaPlayer;
            _vm.VideoViewLoaded();
        };

        _vm.VideoAvailableChanged += (_, hasVideo) =>
        {
            videoView.IsVisible = hasVideo;
        };
    }
    private void SetNavigationButtons()
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        PreviousButton.Content = vm.BackIcon;
        NextButton.Content = vm.ForwardIcon;
        ShuffleCheckbox.Content = vm.ShuffleIcon;
    }

    private void SetPlayButton(int counter)
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        if (counter == 0)
            PlayButton.Content = vm.PlayIcon;
        else
            PlayButton.Content = vm.PauseIcon;
    }

    private void SetImageIcons()
    {
        if (DataContext is not MediaPlayerControlViewModel vm) return;
        SongIcon.Source = vm.SongIcon;
        VolumeIcon.Source = vm.VolumeIcon;
    }
}