using System;
using System.IO;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class MainWindow : Window
{
    private MainWindowViewModel _vm;
    
    public MainWindow()
    {
        InitializeComponent();

        _vm = new MainWindowViewModel();
        
        DataContext = _vm;
        
        GetHealthItem.Click += async (sender, args) =>
        {
            await _vm.GetHealth();
            var messageBox = new MassageBox(_vm.HealthCheckResult);
            await messageBox.ShowDialog(this);
        };
        
        Closed += OnClosed;
    }
    
    private void OnClosed(object? sender, System.EventArgs e)
    {
        var jsonFilePath = Path.Combine(AppData.DataPath, "downloadedMedias.json");
        DownloadedMedia.SaveMediasToJson(AppData.DownloadedMedias, jsonFilePath);
    }

    private async void MediaDoubleClick(object? sender, RoutedEventArgs e)
    {
        try
        {
            if (sender is Border { DataContext: DownloadedMedia media })
            {
                if (!File.Exists(media.DownloadPath))
                {
                    media.IsPlayable = false;
                    throw new Exception("Media not found");
                }
                
                var mediaPlayerWindow = new MediaPlayerWindow(media.DownloadPath);
                await mediaPlayerWindow.ShowDialog(this);
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            AppLogger logger = new();
            logger.LogNewMassage(log);
            
            var messageBox = new MassageBox("An error occurred while trying to play the media: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }
}