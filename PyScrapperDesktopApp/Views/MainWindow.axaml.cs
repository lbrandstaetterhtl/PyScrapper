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
    private readonly AppLogger _logger = new();
    
    public MainWindow()
    {
        InitializeComponent();

        _vm = new MainWindowViewModel();
        
        DataContext = _vm;
        
        Closed += OnClosed;
    }
    
    private void OnClosed(object? sender, EventArgs e)
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
                mediaPlayerWindow.Show();
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to play the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while trying to play the media: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }

    private async void CopyStringToClipboard(string text)
    {
        try
        {
            var clipboard = GetTopLevel(this)?.Clipboard;

            if (clipboard == null)
            {
                throw new Exception("Clipboard is not available");
            }
            
            await clipboard.SetTextAsync(text);
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while trying to copy the download path: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while trying to copy the download path: " + ex.Message);
            await messageBox.ShowDialog(this);
        }
    }
    
    private void CopyDownloadPathClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            CopyStringToClipboard(media.DownloadPath);
        }
    }
    
    private void CopyUrlClick(object? sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            CopyStringToClipboard(media.Url);
        }
    }
}