// csharp
// Datei: Views/MediaPlayerWindow.axaml.cs
using System;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaPlayerWindow : Window
{
    private readonly MediaPlayerWindowViewModel _vm;
    private CancellationTokenSource? _seekCts;

    public MediaPlayerWindow(string path)
    {
        InitializeComponent();

        _vm = new MediaPlayerWindowViewModel(new AudioPlayer(), path);
        DataContext = _vm;

        // Benutzer beginnt ziehen
        SeekSlider.PointerPressed += (_, _) => _vm.BeginScrub();

        // Während ziehen: nur UI-Update
        SeekSlider.PointerMoved += (_, _) =>
        {
            if (_vm.IsScrubbing)
                _vm.ScrubTo(SeekSlider.Value);
        };

        // Loslassen: finaler Seek (während Scrub)
        SeekSlider.PointerReleased += async (_, _) =>
        {
            if (_vm.IsScrubbing)
            {
                // kleine Debounce/Smoothing: falls viele Releases auftreten, nur letzter zählt
                _seekCts?.Cancel();
                _seekCts?.Dispose();
                var cts = new CancellationTokenSource();
                _seekCts = cts;
                try
                {
                    await Task.Delay(80, cts.Token); // sehr kurz, verhindert Doppel-Seeks
                    if (!cts.IsCancellationRequested)
                        _vm.EndScrub(); // EndScrub führt finalen Seek aus
                }
                catch (TaskCanceledException) { }
            }
        };

        // Falls Pointer-Capture verloren geht
        SeekSlider.PointerCaptureLost += (_, _) =>
        {
            if (_vm.IsScrubbing)
                _vm.EndScrub();
        };

        // Keyboard: Enter als Commit (wenn Slider fokusiert)
        SeekSlider.KeyUp += (_, e) =>
        {
            if (e.Key == Key.Enter)
            {
                // Direkter Seek bei Tastatur-Commit (kein Drag)
                _vm.SeekToSeconds(SeekSlider.Value);
            }
        };

        Closed += (_, _) =>
        {
            _seekCts?.Cancel();
            _vm.Dispose();
        };
    }
}
