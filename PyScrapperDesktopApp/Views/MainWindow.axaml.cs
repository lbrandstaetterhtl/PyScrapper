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
        if (Design.IsDesignMode) return;
        
        InitializeComponent();

        _vm = new MainWindowViewModel();
        
        DataContext = _vm;
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
    
    private void DeleteMedia(object sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            AppData.RemoveDownloadedMedia(media);
            
            var log = new Massage("Media removed from the list: " + media.Url, DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("Media removed from the list: " + media.Url);
            messageBox.ShowDialog(this);
        }
    }
    
    private void DeleteFile(object sender, RoutedEventArgs e)
    {
        if (sender is MenuItem { DataContext: DownloadedMedia media })
        {
            try
            {
                if (File.Exists(media.DownloadPath))
                {
                    File.Delete(media.DownloadPath);
                    
                    var log = new Massage("File deleted successfully: " + media.DownloadPath, DateTime.Now, "INFO");
                    _logger.LogNewMassage(log);
                    
                    var messageBox = new MessageBox("File deleted successfully: " + media.DownloadPath);
                    messageBox.ShowDialog(this);
                }
                else
                {
                    throw new Exception("File not found");
                }
            }
            catch (Exception ex)
            {
                var log = new Massage("An error occurred while trying to delete the file: " + ex.Message, DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                
                var messageBox = new MessageBox("An error occurred while trying to delete the file: " + ex.Message);
                messageBox.ShowDialog(this);
            }
        }
    }
}