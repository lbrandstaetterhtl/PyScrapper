using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class FilterWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string? _searchQuery = null;

    [ObservableProperty] 
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes;

    [ObservableProperty] private List<string>? _selectedMediaTypes = null;
    
    [ObservableProperty]
    private DateTimeOffset? _startDate = null;
    
    [ObservableProperty]
    private DateTimeOffset? _endDate = null;

    [ObservableProperty] 
    private bool _isPlayable;
    
    public Action? CloseRequested { get; set; }

    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }

    [RelayCommand]
    private async Task Apply()
    {
        if (AvailableMediaTypes.Contains(SelectedMediaTypes?.FirstOrDefault() ?? string.Empty) == false)
        {
            SelectedMediaTypes = null;
        }
        
        var filter = MediaFilter.BuildMediaFilter(SearchQuery, SelectedMediaTypes, StartDate, EndDate, IsPlayable);
        
        await MediaFilter.ApplyMediaFilter(filter);
        
        CloseRequested?.Invoke();
    }

    public FilterWindowViewModel()
    {
        if (AppData.FilterEnabled)
        {
            AppData.DownloadedMedias.Clear();
            foreach (var media in AppData.OriginalDownloadedMedias)
            {
                AppData.AddDownloadedMedia(media);
            }
            
            var searchQuery = AppData.CurrentMediaFilter.SearchQuery;
            var mediaTypes = AppData.CurrentMediaFilter.MediaTypes;
            var startDate = AppData.CurrentMediaFilter.StartDate;
            var endDate = AppData.CurrentMediaFilter.EndDate;
            var isPlayable = AppData.CurrentMediaFilter.IsPlayable;
            
            Dispatcher.UIThread.Post(() =>
            {
                SearchQuery = searchQuery;
                SelectedMediaTypes = mediaTypes;
                StartDate = startDate;
                EndDate = endDate;
                IsPlayable = isPlayable;
            });
        }
    }
}