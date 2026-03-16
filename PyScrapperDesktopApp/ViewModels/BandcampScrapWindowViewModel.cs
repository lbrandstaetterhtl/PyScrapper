using System.Collections.Generic;
using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class BandcampScrapWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _searchQuery;

    [ObservableProperty]
    private string _searchResultsCount;

    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _Items = new();
    
    [ObservableProperty]
    private List<ApiClient.SearchResultItem> _selectedItems = new();
    
    [ObservableProperty]
    private Window _ScrapWindow;
    
    public RelayCommand CancelCommand { get; set; }

    [RelayCommand]
    private void Scrap()
    {
        var client = new ApiClient();
    }

}