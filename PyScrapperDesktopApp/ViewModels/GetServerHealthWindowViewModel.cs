using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// Class responsible for managing the state and logic of the GetServerHealthWindow, which displays the health status of a server by periodically fetching data from an API endpoint. It handles the connection status, uptime, memory usage, active processes, download jobs, and error messages, updating the UI accordingly.
/// The class also manages cancellation of the health check when the window is closed.
/// </summary>
public partial class GetServerHealthWindowViewModel : ObservableObject
{
    private readonly ApiClient _apiClient;
    private readonly AppLogger _logger = new();

    private CancellationTokenSource _cts;
    
    [ObservableProperty]
    private string _connectionStatus = "Checking server health...";
    
    [ObservableProperty]
    private string _uptimeFormatted = "N/A";
    
    [ObservableProperty]
    private string _memoryFormatted = "N/A";

    [ObservableProperty]
    private int _pid;
    
    [ObservableProperty]
    private ObservableCollection<ApiClient.ServerProcess> _processes = new();
    
    [ObservableProperty]
    private ObservableCollection<ApiClient.DownloadJobItem> _downloadJobs = new();
    
    [ObservableProperty]
    private int _downloadsCount;
    
    [ObservableProperty]
    private ObservableCollection<string> _errorMessages = new();
    
    [ObservableProperty]
    private int _errorsCount;
    
    [ObservableProperty]
    private string _lastHealthCheckTime = "N/A";

    [ObservableProperty]
    private Bitmap _serverStatusIcon = new Bitmap(Path.Combine(AppData.AssetPath, "GetHealth", "load.png"));
    
    public event Action? CloseRequested;
    
    private int _runCount = 0;
    
    private DialogService _dialogService;
    
    public GetServerHealthWindowViewModel(DialogService dialogService)
    {
        _dialogService = dialogService;
        _apiClient = new ApiClient(_dialogService);
    }
    
    /// <summary>
    /// Starts the health check process by creating a cancellation token and running a loop that periodically fetches the server's health status from the API. The loop updates the connection status, uptime, memory usage, active processes, download jobs, and error messages based on the response from the server. If an error occurs during the health check, it sets the status to offline and logs the error message. T
    /// the health check runs every 5 seconds until it is canceled when the window is closed.
    /// </summary>
    /// <exception cref="Exception"></exception>
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
                    var health = await _apiClient.GetHealth(logHealthResponse);

                    if (health != null)
                    {
                        Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                        {
                            ServerStatusIcon = new Bitmap(Path.Combine(AppData.AssetPath, "GetHealth", health.Ok ? "check.png" : "cross.png"));
                            ConnectionStatus = health.Ok ? "Server is reachable" : "Server is not reachable";
                            UptimeFormatted = TimeSpan.FromSeconds(health.UptimeSeconds).ToString(@"dd\.hh\:mm\:ss");
                            MemoryFormatted = $"{health.MemoryMb} MB";
                            Pid = health.Pid;
                            Processes = new ObservableCollection<ApiClient.ServerProcess>(health.Processes);
                            DownloadJobs = new ObservableCollection<ApiClient.DownloadJobItem>(health.ActiveDownloads);
                            DownloadsCount = health.ActiveDownloads.Count;
                            ErrorMessages = new ObservableCollection<string>(health.ErrorMessages);
                            ErrorsCount = health.ErrorMessages.Count;
                            LastHealthCheckTime = "Last check: " + DateTime.Now.ToString("HH:mm:ss");
                        });
                    }
                    else
                    {
                        throw new Exception("Server is not reachable");
                    }
                }
                catch (Exception e)
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(SetOffline);
                    
                    var log = new Massage("Health check failed: " + e.Message, DateTime.Now, "ERROR");
                    _logger.LogNewMassage(log);
                }

                _runCount++;
                
                await Task.Delay(5000, token).WaitAsync(token);
            }
        }, token);
    }
    
    /// <summary>
    /// Sets the status of the server to offline by updating the connection status, status color, uptime, memory usage, process ID, active processes, download jobs, and error messages to indicate that the server is not reachable. This method is called when an error occurs during the health check to reflect the offline status in the UI and log the error message.
    /// It also updates the last health check time to indicate when the last attempt was made to check the server's health.
    /// </summary>
    private void SetOffline()
    {
        ServerStatusIcon = new Bitmap(Path.Combine(AppData.AssetPath, "GetHealth", "cross.png"));
        ConnectionStatus = "Server is not reachable";
        UptimeFormatted = "N/A";
        MemoryFormatted = "N/A";
        Pid = 0;
        Processes.Clear();
        DownloadJobs.Clear();
        DownloadsCount = 0;
        ErrorMessages.Clear();
        ErrorsCount = 0;
        LastHealthCheckTime = "Last attempt: " + DateTime.Now.ToString("HH:mm:ss");
    }
    
    /// <summary>
    /// Stops the health check process by canceling the cancellation token and invoking the CloseRequested event to signal that the window should be closed. This method is called when the user closes the window or when an error occurs that requires stopping the health check, ensuring that any ongoing tasks are properly canceled and resources are released.
    /// It also allows for any necessary cleanup actions to be performed before the window is closed.
    /// </summary>
    public void StopHealthCheck()
    {
        _cts.Cancel();
    }
    
    /// <summary>
    /// Closes the GetServerHealthWindow by stopping the health check process and invoking the CloseRequested event. This method is called when the user clicks the close button on the window, ensuring that any ongoing health check tasks are properly canceled and that the window is closed gracefully.
    /// It also allows for any necessary cleanup actions to be performed before the window is closed, such as releasing resources or saving state if needed.
    /// </summary>
    [RelayCommand]
    private void Close()
    {
        StopHealthCheck();
        CloseRequested?.Invoke();
    }
}