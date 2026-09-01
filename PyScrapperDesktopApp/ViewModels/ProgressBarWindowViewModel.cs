using System;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// ProgressBarWindowViewModel is a ViewModel class that manages the state and logic for a progress bar window in a desktop application.
/// It interacts with an API client to fetch download progress data and updates the UI accordingly.
/// The class also handles cancellation of the progress tracking and provides a mechanism to close the window when the download is complete or when an error occurs.
/// </summary>
public partial class ProgressBarWindowViewModel : ObservableObject
{
    private readonly ApiClient _apiClient;
    private CancellationTokenSource? _cts;

    [ObservableProperty] 
    private string _progress;
    
    [ObservableProperty]
    private string _status;
    
    [ObservableProperty]
    private string _progressSpeed;

    [ObservableProperty] 
    private string _eta;
    
    [ObservableProperty]
    private bool _isFinished = false;
    
    private readonly AppLogger _logger = AppLogger.Instance;
    
    /// <summary>
    /// Constructor for the ProgressBarWindowViewModel class, which initializes the API client used for fetching download progress data. This class is responsible for managing the state and logic of a progress bar window that displays the download progress, status, and speed of a download operation.
    /// It also handles cancellation of the progress tracking when necessary.
    /// </summary>
    public ProgressBarWindowViewModel()
    {
        _apiClient = new ApiClient();
    }

    /// <summary>
    /// StartProgress method that initiates the tracking of download progress for a given download ID. It runs a background task that periodically fetches the download progress data from the API and updates the UI accordingly.
    /// The method also handles cancellation of the progress tracking and error handling, updating the status message and logging any errors encountered during the process.
    /// </summary>
    /// <param name="id"></param>
    /// <returns name="errorWhileDownloading"></returns>
    /// <exception cref="Exception"></exception>
    public Task<bool> StartProgress(DownloadResource resource)
    {
        try
        {
            try
            {
                if (Design.IsDesignMode) return Task.FromResult(true);

                bool errorWhileDownloading = false;
                _cts = new CancellationTokenSource();
                var token = _cts.Token;

                Task.Run(async () =>
                {
                    while (!IsFinished)
                    {
                        if (token.IsCancellationRequested)
                            break;

                        try
                        {
                            var progressResponse = _apiClient.GetDownloadProgress(resource);
                            var progressData = progressResponse.Result;

                            if (progressData == null) throw new Exception("Failed to get progress data");

                            Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                            {
                                if (progressData.TotalBytes != -1)
                                {
                                    if (progressData.ErrorMessage is not "")
                                    {
                                        Status = $"Error: {progressData.ErrorMessage}";
                                        var log = new Message(progressData.ErrorMessage, DateTime.Now, "ERROR");
                                        _logger.LogNewMassage(log);
                                        errorWhileDownloading = true;
                                        StopProgress();
                                    }
                                    else
                                    {
                                        Status = progressData.Status + " | please wait...";
                                    }

                                    Progress = $"{progressData.DownloadProgress}%";
                                    ProgressSpeed = $"{progressData.Speed} Mb/s";
                                    Eta = $"{progressData.Eta} seconds";

                                    if (progressData.Status.Equals("finished"))
                                    {
                                        IsFinished = true;
                                        Status = "Finished";
                                        ProgressSpeed = "0 Mb/s";
                                        Eta = "0 seconds";
                                        StopProgress();
                                        Task.Delay(3500).Wait();
                                        CloseRequested?.Invoke();
                                    }
                                }
                                else
                                {
                                    if (progressData.ErrorMessage is not "")
                                    {
                                        Status = $"Error: {progressData.ErrorMessage}";
                                        var log = new Message(progressData.ErrorMessage, DateTime.Now, "ERROR");
                                        _logger.LogNewMassage(log);
                                        errorWhileDownloading = true;
                                        StopProgress();
                                    }
                                    else
                                    {
                                        Status = progressData.Status + " | please wait...";
                                    }

                                    Progress = $"{progressData.DownloadProgress}%";
                                    ProgressSpeed = $"{progressData.Speed} Mb/s";
                                    Eta = $"{progressData.Eta} seconds";

                                    if (progressData.Status.Equals("finished"))
                                    {
                                        IsFinished = true;
                                        Status = "Finished";
                                        ProgressSpeed = "0 Mb/s";
                                        Eta = "0 seconds";
                                        StopProgress();
                                        Task.Delay(3500).Wait();
                                        CloseRequested?.Invoke();
                                    }
                                }
                            });
                        }
                        catch (OperationCanceledException)
                        {
                            var log = new Message("Progress tracking cancelled", DateTime.Now, "INFO");
                            _logger.LogNewMassage(log);
                            break;
                        }
                        catch (Exception e)
                        {
                            Avalonia.Threading.Dispatcher.UIThread.Post(() => { Status = $"Error: {e.Message}"; });
                        }

                        try
                        {
                            await Task.Delay(1000, token);
                        }
                        catch (OperationCanceledException)
                        {
                            var log = new Message("Progress tracking cancelled during delay", DateTime.Now, "INFO");
                            _logger.LogNewMassage(log);
                            break;
                        }
                    }
                }, token);

                return Task.FromResult(errorWhileDownloading);
            }
            catch (Exception e)
            {
                var log = new Message("Error while tracking progress: " + e.Message, DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
            
                Avalonia.Threading.Dispatcher.UIThread.Post(() => { Status = $"Error: {e.Message}"; });

                return Task.FromResult(true);
            }
        }
        catch (Exception exception)
        {
            return Task.FromException<bool>(exception);
        }
    }

    /// <summary>
    /// Stops the progress tracking by canceling the associated CancellationTokenSource, which signals the background task to stop fetching progress data and exit gracefully.
    /// This method is called when the download is complete or when an error occurs, ensuring that resources are properly released and the UI is updated accordingly.
    /// </summary>
    private void StopProgress()
    {
        _cts?.Cancel();
    }

    /// <summary>
    /// Closes the ProgressBarWindow by invoking the CloseRequested event, which signals that the window should be closed. This method is called when the user clicks the close button on the window or when the download is complete, ensuring that any ongoing progress tracking tasks are properly canceled and that the window is closed gracefully.
    /// </summary>
    [RelayCommand]
    private void Close()
    {
        _cts.Cancel();
        _cts.Dispose();
        CloseRequested!.Invoke();
    }
    
    /// <summary>
    /// Waits until the download is finished by periodically checking the IsFinished property. This method can be used to block the calling thread until the download process is complete, allowing for any necessary cleanup actions to be performed after the download finishes.
    /// </summary>
    public async Task WaitUntilFinished()
    {
        while (!IsFinished)
        {
            await Task.Delay(500);
        }
    }
    
    public event Action? CloseRequested;
}