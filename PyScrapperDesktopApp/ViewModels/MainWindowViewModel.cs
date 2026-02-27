using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;


public partial class MainWindowViewModel : INotifyPropertyChanged
{
    private ObservableCollection<DownloadedMedia> _downloadedMediaList;
    
    private string _healthCheckResult;

    public ObservableCollection<DownloadedMedia> DownloadedMediaList
    {
        get => _downloadedMediaList;
        set
        {
            _downloadedMediaList = value;
            OnPropertyChanged(nameof(DownloadedMediaList));
        }
    }

    public string HealthCheckResult
    {
        get => _healthCheckResult;
        set
        {
            _healthCheckResult = value;
            OnPropertyChanged(nameof(HealthCheckResult));
        }
    }

    public MainWindowViewModel()
    {
        DownloadedMediaList = AppData.DownloadedMedias;
    }
    
    public event PropertyChangedEventHandler? PropertyChanged;
    
    private void OnPropertyChanged(string propertyName)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
    
    [RelayCommand]
    public async Task OpenSunoScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var sunoScrapWindow = new Views.SunoScrapWindow();
        await sunoScrapWindow.ShowDialog(desktop.MainWindow);
    }
    
    [RelayCommand]
    public async Task GetHealth()
    {
        ApiClient client = new();
        
        var serverUrl = "127.0.0.1:8765";
        
        var health = await client.GetHealth(serverUrl);
        
        var processString = health?.Processes != null
            ? "-----" + string.Join("\n -----", health.Processes.Select(p => $"{p.Name} (PID: {p.Pid})"))
            : "No processes information available";
        
        HealthCheckResult = $"Server health check successful: \n \n --Uptime: {health?.UptimeSeconds} seconds \n | \n --Memory: {health?.MemoryMb} MB \n | \n --PID: {health?.Pid} \n | \n --Processes {health?.Processes.Count}: \n {processString}";
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
            var messageBox = new MassageBox("File does not exist. Please check the path and try again.");
            await messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
            
        var mediaPlayerWindow = new MediaPlayerWindow(path);
        await mediaPlayerWindow.ShowDialog(desktop.MainWindow);
    }
}