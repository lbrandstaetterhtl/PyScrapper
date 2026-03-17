using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Interactivity;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;


public partial class MainWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private ObservableCollection<DownloadedMedia> _downloadedMediaList;

    public MainWindowViewModel()
    {
        if (Design.IsDesignMode) return;
        
        DownloadedMediaList = AppData.DownloadedMedias;
    }
    
    [RelayCommand]
    private async Task OpenSunoScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var sunoScrapWindow = new Views.SunoScrapWindow();
        await sunoScrapWindow.ShowDialog(desktop.MainWindow);
    }
    
    [RelayCommand]
    public void GetHealth()
    {
        if (Design.IsDesignMode) return;
        
        var getHealthWindow = new GetServerHealthWindow();
        getHealthWindow.Show();
    }
    
    [RelayCommand]
    public async Task OpenMediaPlayerWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;

        var path = await new InputWindow("Enter a valid file path (.mp3)").ShowDialog<string>(desktop.MainWindow);

        if (path == null)
        {
            return;
        }
        
        if (!File.Exists(path))
        {
            var messageBox = new MessageBox("File does not exist. Please check the path and try again.");
            await messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
            
        var mediaPlayerWindow = new MediaPlayerWindow(path);
        mediaPlayerWindow.Show();
    }

    [RelayCommand]
    private async Task OpenYoutubeScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var youtubeScrapWindow = new ScrapWindowWithSearch("youtube");
        await youtubeScrapWindow.ShowDialog(desktop.MainWindow);
    }

    [RelayCommand]
    private async Task OpenBandcampScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;

        var bandcampScrapWindow = new ScrapWindowWithSearch("bandcamp");
        await bandcampScrapWindow.ShowDialog(desktop.MainWindow);
    }
}