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
    
    public ProgressBarWindowViewModel(string id)
    {
        _apiClient = new ApiClient();
        StartProgress(id);
    }

    public void StartProgress(string id)
    {
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
                    
                    Avalonia.Threading.Dispatcher.UIThread.Post(() =>
                    {
                        Progress = progressData.DownloadProgress;
                        Status = progressData.Status;
                        ProgressSpeed = progressData.Speed;
                        
                        if (progressData.ErrorMessage is not "")
                        {
                            Status = $"Error: {progressData.ErrorMessage}";
                            var log = new Massage(progressData.ErrorMessage, DateTime.Now, "ERROR");
                            new AppLogger().LogNewMassage(log);
                            StopProgress();
                        } 

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
    }

    public void StopProgress()
    {
        _cts?.Cancel();
    }

    [RelayCommand]
    public void Close()
    {
        CloseRequested.Invoke();
    }
    
    
    public event Action? CloseRequested;
}