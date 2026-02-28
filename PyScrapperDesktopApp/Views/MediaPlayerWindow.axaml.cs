// csharp
// Datei: Views/MediaPlayerWindow.axaml.cs
using System;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Threading;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaPlayerWindow : Window
{
    private readonly MediaPlayerWindowViewModel _vm;
    private CancellationTokenSource? _seekCts;
    
    private CancellationTokenSource? _holdCts; 

    public MediaPlayerWindow(string path)
    {
        InitializeComponent();

        _vm = new MediaPlayerWindowViewModel(new AudioPlayer(), path);
        DataContext = _vm;

        SeekSlider.PointerPressed += (_, _) =>
        {
            _vm._audioPlayer.TimeMS = (int)(SeekSlider.Value * 1000);
            _vm.BeginScrub();
        };

        SeekSlider.PointerReleased += async (_, _) =>
        {
            if (_vm.IsScrubbing)
            {
                _vm._audioPlayer.TimeMS = (int)(SeekSlider.Value * 1000);
                _seekCts?.Cancel();
                _seekCts?.Dispose();
                var cts = new CancellationTokenSource();
                _seekCts = cts;
                try
                {
                    if (!cts.IsCancellationRequested)
                        _vm.EndScrub();
                }
                catch (TaskCanceledException) { }
            }
        };
        VolumeSlider.ValueChanged += (_, _) =>
        {
            if (VolumeSlider.IsPointerOver)
                _vm._audioPlayer.Volume = (int)VolumeSlider.Value;
        };

        SeekSlider.PointerCaptureLost += (_, _) =>
        {
            _vm._audioPlayer.TimeMS = (int)(SeekSlider.Value * 1000);
            if (_vm.IsScrubbing)
                _vm.EndScrub();
        };
        
        ForwardButton.PointerPressed += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            var cts = new CancellationTokenSource();
            _holdCts = cts;

            Dispatcher.UIThread.Post(() => _vm.ScrubTo(SeekSlider.Value + 1));

            Task.Run(async () =>
            {
                try
                {
                    while (!cts.IsCancellationRequested)
                    {
                        await Task.Delay(1000, cts.Token);
                        if (cts.IsCancellationRequested) break;
                        await Dispatcher.UIThread.InvokeAsync(() => _vm.ScrubTo(SeekSlider.Value + 1));
                    }
                }
                catch (TaskCanceledException) { }
            });
        };

        ForwardButton.PointerReleased += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            _holdCts = null;
        };

        ForwardButton.PointerCaptureLost += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            _holdCts = null;
        };

        BackwardButton.PointerPressed += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            var cts = new CancellationTokenSource();
            _holdCts = cts;

            Dispatcher.UIThread.Post(() => _vm.ScrubTo(SeekSlider.Value - 1));

            Task.Run(async () =>
            {
                try
                {
                    while (!cts.IsCancellationRequested)
                    {
                        await Task.Delay(1000, cts.Token);
                        if (cts.IsCancellationRequested) break;
                        await Dispatcher.UIThread.InvokeAsync(() => _vm.ScrubTo(SeekSlider.Value - 1));
                    }
                }
                catch (TaskCanceledException) { }
            });
        };

        BackwardButton.PointerReleased += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            _holdCts = null;
        };

        BackwardButton.PointerCaptureLost += (_, _) =>
        {
            _holdCts?.Cancel();
            _holdCts?.Dispose();
            _holdCts = null;
        };

        Closed += (_, _) =>
        {
            
            _seekCts?.Cancel();
            _holdCts?.Cancel();
            _seekCts?.Dispose();
            _holdCts?.Dispose();
            _vm.Dispose();
        };
        
        CloseButton.Click += (_, _) => Close();
    }
}
