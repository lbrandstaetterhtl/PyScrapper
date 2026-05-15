using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class FilterWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _searchQuery;

    [ObservableProperty] 
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes;
    
    [ObservableProperty]
    private List<string> _selectedMediaTypes;
    
    [ObservableProperty]
    private DateTimeOffset? _startDate;
    
    [ObservableProperty]
    private DateTimeOffset? _endDate;

    [ObservableProperty] 
    private bool _isPlayable;
    
    public Action? CloseRequested { get; set; }

    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }

    [RelayCommand]
    private void Apply()
    {
        AppData.FilterEnabled = true;

        var filteredMedias = AppData.DownloadedMedias.Where(m =>
            (!IsPlayable || m.IsPlayable == IsPlayable) &&
            (StartDate == null || m.DownloadedAt >= StartDate) &&
            (EndDate == null || m.DownloadedAt <= EndDate) &&
            (SelectedMediaTypes == null || !SelectedMediaTypes.Any() || SelectedMediaTypes.Contains(m.MediaType)) &&
            (string.IsNullOrEmpty(SearchQuery) || m.Title.Contains(SearchQuery, StringComparison.OrdinalIgnoreCase))
        ).ToList();
        
        AppData.DownloadedMedias.Clear();

        foreach (var media in filteredMedias)
        {
            AppData.AddDownloadedMedia(media);
        }
        
        CloseRequested?.Invoke();
    }
}