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
    private CancellationTokenSource _cts;

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
    
    private Window _window;
    
    /// <summary>
    /// Constructor for the ProgressBarWindowViewModel class, which initializes the API client used for fetching download progress data. This class is responsible for managing the state and logic of a progress bar window that displays the download progress, status, and speed of a download operation.
    /// It also handles cancellation of the progress tracking when necessary.
    /// </summary>
    public ProgressBarWindowViewModel(Window window)
    {
        _apiClient = new ApiClient();
        _window = window;
    }

    /// <summary>
    /// StartProgress method that initiates the tracking of download progress for a given download ID. It runs a background task that periodically fetches the download progress data from the API and updates the UI accordingly.
    /// The method also handles cancellation of the progress tracking and error handling, updating the status message and logging any errors encountered during the process.
    /// </summary>
    /// <param name="id"></param>
    /// <returns name="errorWhileDownloading"></returns>
    /// <exception cref="Exception"></exception>
   public async Task<string> StartProgress(DownloadResource resource, Task<string> downloadTask, CancellationTokenSource cts)
    {
        if (Design.IsDesignMode)
            return "";

        string result = "";
        CancellationToken token = cts.Token;

        var progressTask = Task.Run (async () =>
        {
            try
            {
                while (!IsFinished && !token.IsCancellationRequested)
                {
                    var progressData =
                        await _apiClient.GetDownloadProgress(resource);

                    if (progressData == null)
                        throw new Exception("Failed to get progress data");

                    await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        if (!string.IsNullOrEmpty(progressData.ErrorMessage))
                        {
                            Status = $"Error: {progressData.ErrorMessage}";

                            _logger.LogNewMassage(new Message(
                                progressData.ErrorMessage,
                                DateTime.Now,
                                "ERROR"));
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
                        }
                    });

                    if (IsFinished)
                    {
                        await Task.Delay(3500, token);

                        await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() => CloseRequested?.Invoke());

                        break;
                    }

                    await Task.Delay(1000, token);
                }
            }
            catch (OperationCanceledException)
            {
                // Der Benutzer hat den Vorgang abgebrochen.
            }
            catch (Exception e)
            {
                await Avalonia.Threading.Dispatcher.UIThread.InvokeAsync(() => { Status = $"Error: {e.Message}"; });

                _logger.LogNewMassage(new Message(
                    "Error while tracking progress: " + e.Message,
                    DateTime.Now,
                    "ERROR"));
            }
        }, token);
        
        await Task.WhenAll(progressTask, downloadTask);

        return await downloadTask;
    }

    [RelayCommand]
    private void Cancel()
    {
        var progressBarWindow = _window as ProgressBarWindow;
        progressBarWindow?.OnCancel.Invoke();
        CloseRequested?.Invoke();
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