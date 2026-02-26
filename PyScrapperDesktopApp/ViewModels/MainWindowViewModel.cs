using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MainWindowViewModel : INotifyPropertyChanged
{
    private ObservableCollection<DownloadedMedia> _downloadedMediaList;

    public ObservableCollection<DownloadedMedia> DownloadedMediaList
    {
        get => _downloadedMediaList;
        set
        {
            _downloadedMediaList = value;
            OnPropertyChanged(nameof(DownloadedMediaList));
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
        
        var SunoScrapWindow = new Views.SunoScrapWindow();
        await SunoScrapWindow.ShowDialog(desktop.MainWindow);
    }
}