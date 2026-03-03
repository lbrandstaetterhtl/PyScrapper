using System;
using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class YoutubeScrapWindow : Window
{
    public YoutubeScrapWindow()
    {
        InitializeComponent();
        
        var vm = new YoutubeScrapWindowViewModel(this);
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}