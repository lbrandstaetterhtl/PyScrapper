using System;
using System.Collections.ObjectModel;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class GetServerHealthWindowViewModel : ObservableObject
{
    private readonly ApiClient _apiClient = new();
    private readonly AppLogger _logger = new();

    private CancellationTokenSource _cts;

    private const string ServerUrl = "127.0.0.1:8765";
    
    [ObservableProperty]
    private string _connectionStatus = "Checking server health...";
    
    [ObservableProperty]
    private string _uptimeFormatted = "N/A";
    
    [ObservableProperty]
    private string _memoryFormatted = "N/A";

    [ObservableProperty]
    private int pid;
    
    [ObservableProperty]
    private ObservableCollection<ApiClient.ServerProcess> _processes = new();
    
    [ObservableProperty]
    private ObservableCollection<ApiClient.DownloadJob> _downloadJobs = new();
    
    [ObservableProperty]
    private int _downloadsCount;
    
    [ObservableProperty]
    private ObservableCollection<string> _errorMessages = new();
    
    [ObservableProperty]
    private int _errorsCount;
    
    [ObservableProperty]
    private string _lastHealthCheckTime = "N/A";
    
    [ObservableProperty]
    private IBrush _statusColor = Brushes.Gray;
    
    public event Action? CloseRequested;
    
    private int _runCount = 0;
    
    public void StartHealthCheck()
    {
        _cts = new CancellationTokenSource();
        
        var token = _cts.Token;
        
        if (Design.IsDesignMode)
        {
            _cts.Cancel();
            _cts.Dispose();
            return;
        }

        Task.Run(async () =>
        {
            _runCount = 0;
            
            while (!token.IsCancellationRequested)
            { 
                bool logHealthResponse = _runCount % 5 == 0;
                
                try
                {
                    var health = await _apiClient.GetHealth(ServerUrl, logHealthResponse);

                    if (health != null)
                    {
                        ConnectionStatus = health.Ok ? "Server is reachable" : "Server is not reachable";
                        StatusColor = health.Ok ? Brushes.LightGreen : Brushes.LightCoral;
                        UptimeFormatted = TimeSpan.FromSeconds(health.UptimeSeconds).ToString(@"dd\.hh\:mm\:ss");
                        MemoryFormatted = $"{health.MemoryMb} MB";
                        Pid = health.Pid;
                        Processes = new ObservableCollection<ApiClient.ServerProcess>(health.Processes);
                        DownloadJobs = new ObservableCollection<ApiClient.DownloadJob>(health.ActiveDownloads);
                        DownloadsCount = health.ActiveDownloads.Count;
                        ErrorMessages = new ObservableCollection<string>(health.ErrorMessages);
                        ErrorsCount = health.ErrorMessages.Count;
                        LastHealthCheckTime = "Last check: " + DateTime.Now.ToString("HH:mm:ss");
                    }
                    else
                    {
                        throw new Exception("Server is not reachable");
                    }
                }
                catch (Exception e)
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        SetOffline(e.Message);
                    });
                    
                    var log = new Massage("Health check failed: " + e.Message, DateTime.Now, "ERROR");
                    _logger.LogNewMassage(log);
                }

                _runCount++;
            }
        }, token);
    }
    
    private void SetOffline(string reason)
    {
        ConnectionStatus = "Server is not reachable";
        UptimeFormatted = "N/A";
        MemoryFormatted = "N/A";
        Pid = 0;
        Processes.Clear();
        DownloadJobs.Clear();
        DownloadsCount = 0;
        ErrorMessages.Clear();
        ErrorsCount = 0;
        LastHealthCheckTime = "Last attempt: " + DateTime.Now.ToString("HH:mm:ss") + " -- " + reason;
    }
    
    public void StopHealthCheck()
    {
        _cts.Cancel();
        CloseRequested?.Invoke();
    }
    
    [RelayCommand]
    private void Close()
    {
        StopHealthCheck();
        CloseRequested?.Invoke();
    }
}