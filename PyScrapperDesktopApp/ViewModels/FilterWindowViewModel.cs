using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
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

    [ObservableProperty]
    private ObservableCollection<string> _selectedMediaTypes = new();
    
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
}