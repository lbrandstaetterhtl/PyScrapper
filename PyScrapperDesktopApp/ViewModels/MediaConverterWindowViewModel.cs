using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MediaConverterWindowViewModel(DialogService ds, Window window) : ObservableObject
{
    [ObservableProperty] 
    private string _filePath = "";

    [ObservableProperty]
    private string _targetContainer = "";
    
    [ObservableProperty]
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes.Keys.ToList();

    [ObservableProperty] private string _selectButtonContent = "Select File";
    
    public event Action? CloseRequested;

    [RelayCommand]
    private async Task OpenFilePicker()
    {
        var topLevel = TopLevel.GetTopLevel(window);
        
        var storageService = new StorageService(topLevel!);

        var files = await storageService.OpenFilePickerAsync(new FilePickerOpenOptions()
        {
            Title = "Open File",
            AllowMultiple = false,
            FileTypeFilter = AppData.FileTypes
        });

        if (files == null || files.Count <= 0) return;
        
        string path = files[0].Path.LocalPath;

        if (!File.Exists(path)) return;
        
        FilePath = path;
        var filename = Path.GetFileName(path);
        SelectButtonContent = $"Selected: {filename}";
    }

    [RelayCommand]
    private async Task Convert()
    {
        var result = await MediaConverter.Convert(FilePath, TargetContainer);
        var filename = Path.GetFileNameWithoutExtension(FilePath);
        var extension = Path.GetExtension(result);

        var createRequestData = new CreateDownloadedMediaRequest()
        {
            UserIdentifier = AppData.CurrentUser.Identifier,
            DownloadedAt = DateTime.Now.ToString("o"),
            DownloadPath = result,
            IsPlayable = File.Exists(result),
            MediaType = extension,
            Title = filename,
            Url = "N/A"
        };
        
        var media = await Database.CreateDownloadedMediaAsync(createRequestData);
        
        AppData.AddDownloadedMedia(media);
        CloseRequested?.Invoke();
    }
    
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}