using System;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class ProgressBarWindowViewModel : ObservableObject
{
    private readonly ApiClient _apiClient;
    private CancellationTokenSource? _cts;

    [ObservableProperty] 
    private float _progress;
    
    [ObservableProperty]
    private string _status;
    
    [ObservableProperty]
    private float _progressSpeed;
    
    [ObservableProperty]
    private bool _isFinished = false;
    
    public ProgressBarWindowViewModel()
    {
        _apiClient = new ApiClient();
    }

    public async Task<bool> StartProgress(string id)
    {
        if (Design.IsDesignMode) return true;
        
        bool errorWhileDownloading = false;
        _cts = new CancellationTokenSource();
        var token = _cts.Token;
        
        Task.Run( async () =>
        {
            while (_progress < 100)
            {
                if (token.IsCancellationRequested)
                    break;
                
                try
                {
                    var progressResponse = _apiClient.GetDownloadProgress(id, "127.0.0.1:8765");
                    var progressData = progressResponse.Result;
                    
                    if (progressData == null) throw new Exception("Failed to get progress data");
                    
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        if (progressData.ErrorMessage is not "")
                        {
                            Status = $"Error: {progressData.ErrorMessage}";
                            var log = new Massage(progressData.ErrorMessage, DateTime.Now, "ERROR");
                            new AppLogger().LogNewMassage(log);
                            errorWhileDownloading = true;
                            StopProgress();
                        }
                        else
                        {
                            Status = progressData.Status;
                        }
                        
                        Progress = progressData.DownloadProgress;
                        ProgressSpeed = progressData.Speed;

                        if (progressData.Status.Equals("complete"))
                        {
                            IsFinished = true;
                            StopProgress();
                        }
                    });
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception e)
                {
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        Status = $"Error: {e.Message}";
                    });
                }
                
                try
                {
                    await Task.Delay(1000, token);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
            }
        }, token);
        
        return errorWhileDownloading;
    }

    private void StopProgress()
    {
        _cts?.Cancel();
    }

    [RelayCommand]
    private void Close()
    {
        CloseRequested!.Invoke();
    }
    
    
    public event Action? CloseRequested;
}