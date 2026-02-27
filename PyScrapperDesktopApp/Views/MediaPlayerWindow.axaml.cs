using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MediaPlayerWindow : Window
{
    public MediaPlayerWindow(string path)
    {
        InitializeComponent();
        
        var vm = new MediaPlayerWindowViewModel(new AudioPlayer(), path);
        DataContext = vm;

        SeekSlider.AddHandler(PointerPressedEvent, (_, _) => vm.IsScrubbing = true);

        SeekSlider.AddHandler(PointerReleasedEvent, (_, _) =>
        {
            vm.IsScrubbing = false;
            vm.SeekToSeconds((long)System.Math.Round(vm.PositionSeconds));
        });
        
        Closed += (_,_) => vm.Dispose();
    }
}