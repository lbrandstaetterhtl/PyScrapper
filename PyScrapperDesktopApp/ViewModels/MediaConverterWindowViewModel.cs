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
    private string _targetContainer = ".mp4";
    
    [ObservableProperty]
    private List<string> _availableMediaTypes = AppData.ValidMediaTypes.Keys.ToList();

    [ObservableProperty] private string _selectButtonContent = "Select File";
    
    private readonly AppLogger _logger = AppLogger.Instance;
    
    public event Action? CloseRequested;

    [RelayCommand]
    private async Task OpenFilePicker()
    {
        try
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

            if (!File.Exists(path)) throw new FileNotFoundException($"File not found at {path}");

            FilePath = path;
            var filename = Path.GetFileName(path);
            SelectButtonContent = $"Selected: {filename}";
        }
        catch (Exception ex)
        {
            await ds.ShowAlertAsync($"Error selecting file: {ex.Message}");
            
            _logger.LogNewMassage(new Message($"Error selecting file: {ex.Message}", DateTime.Now, "ERROR"));
        }
    }

    [RelayCommand]
    private async Task Convert()
    {
        try
        {
            var result = await MediaConverter.Convert(FilePath, TargetContainer);
            
            if (!File.Exists(result)) throw new FileNotFoundException($"Converted file not found at {result}");
            
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
        catch (Exception ex)
        {
            await ds.ShowAlertAsync($"Error converting media: {ex.Message}");
            
            _logger.LogNewMassage(new Message($"Error converting media: {ex.Message}", DateTime.Now, "ERROR"));
        }
    }
    
    [RelayCommand]
    private void Cancel()
    {
        CloseRequested?.Invoke();
    }
}