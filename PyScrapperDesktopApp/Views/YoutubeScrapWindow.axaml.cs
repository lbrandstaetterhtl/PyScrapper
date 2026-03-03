using System;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Data;
using Avalonia.Interactivity;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class YoutubeScrapWindow : Window
{
    private YoutubeScrapWindowViewModel? _vm;
    
    public YoutubeScrapWindow()
    {
        InitializeComponent();
        
        _vm = new YoutubeScrapWindowViewModel(this);
        
        DataContext = _vm;
        
        _vm.RequestClose += Close;
        
        int buttonCount = 0;
        
        EnterButton.Click += (sender, args) =>
        {
            if (buttonCount == 0)
            {
                SearchGrid.IsVisible = false;
                ResultsGrid.IsVisible = true;
                _vm.Search();
                buttonCount++;
            }
        };

        BackToSearch.Click += (sender, args) =>
        {
            if (buttonCount == 1)
            {
                SearchGrid.IsVisible = true;
                ResultsGrid.IsVisible = false;
                buttonCount--;
            }
        };
    }
}