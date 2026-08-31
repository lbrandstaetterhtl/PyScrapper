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
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes.Keys.ToList();

    [ObservableProperty]
    private ObservableCollection<string> _selectedMediaTypes = new();
    
    [ObservableProperty]
    private DateTimeOffset? _startDate = null;
    
    [ObservableProperty]
    private DateTimeOffset? _endDate = null;

    [ObservableProperty] 
    private bool _isPlayable;
    
    public Action? CloseRequested { get; set; }

    /// <summary>
    /// Command method that is executed when the user clicks the "Cancel" button.
    /// It simply invokes the CloseRequested action to signal that the filter window should be closed without applying any changes.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }

    /// <summary>
    /// Command method that is executed when the user clicks the "Apply" button.
    /// It validates the selected media types against the available media types, builds a media filter based on the current filter criteria, applies the filter to the media collection,
    /// and then invokes the CloseRequested action to signal that the filter window should be closed after applying the changes.
    /// </summary>
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