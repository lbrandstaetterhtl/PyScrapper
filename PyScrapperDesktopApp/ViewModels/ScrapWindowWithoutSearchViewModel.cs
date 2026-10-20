using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Xml;
using Avalonia.Controls;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// SunoScrapWindowViewModel is a view model class that manages the data and logic for the Suno scrap window in the PyScrapperDesktopApp.
/// It inherits from ObservableObject, allowing it to notify the view of property changes.
/// The view model contains properties for the Suno URL, selected media type, filename, and a list of available media types.
/// It also includes a command for initiating the scrap process and an event for requesting the closure of the scrap window.
/// The Scrap method handles the scraping logic, including sending a request to the server, showing a progress bar window, and adding the downloaded media to the AppData if successful.
/// If any errors occur during the process, it displays a message box to inform the user.
/// </summary>
public partial class ScrapWindowWithoutSearchViewModel : ObservableObject
{
    [ObservableProperty] private string _url = "";
    
    private readonly List<string> _availableMediaType = AppData.ValidMediaTypes.Keys.ToList();

    [ObservableProperty]
    private string _selectedMediaType = "";


    [ObservableProperty] private string _filename = "";
    public RelayCommand CancelCommand { get; set; }
    
    public IEnumerable<string> AvailableProviders => AppData.ValidProviders;
    
    [ObservableProperty]
    private string _selectedProvider = "";

    public IEnumerable<string> AvailableMediaTypes => _availableMediaType;
    
    public event Action? RequestClose;
    
    private readonly DialogService _dialogService;
    
    private readonly AppLogger _logger = AppLogger.Instance;
    
    private CancellationTokenSource _cts = new CancellationTokenSource();
    
    private Window _scrapWindow;

    private string _path;
    
    [ObservableProperty]
    private bool _autoConvert = false;
    
    /// <summary>
    /// Scrap method that is executed when the user initiates the scraping process.
    /// It creates an instance of the ApiClient and sends a scrap request to the server with the provided URL, media type, filename, and download path.
    /// If the request is successful, it waits for a short delay before showing a progress bar window to track the download progress.
    /// Once the download is complete, it checks if the downloaded file is playable and adds it to the list of downloaded media in the AppData.
    /// If any errors occur during the process, it displays a message box to inform the user.
    /// </summary>
    [RelayCommand]
    private async Task Scrap()
    {
        try
        {
            ApiClient client = new();
            
            
            var topLevel = TopLevel.GetTopLevel(_scrapWindow);
            var storageService = new StorageService(topLevel!);
            var folder = await topLevel.StorageProvider.TryGetFolderFromPathAsync(AppData.Settings.DownloadPath!);

            var options = new FilePickerSaveOptions()
            {
                SuggestedStartLocation = folder,
                SuggestedFileName = $"{Filename}{SelectedMediaType}",
            };

            var file = await storageService.SaveFilePickerAsync(options);

            if (file == null)
            {
                return;
            }
                
            var filename = file.Name.Substring(0, file.Name.LastIndexOf('.'));
            var validFilename = DownloadedMedia.TryValidateFileName(filename, out var errorMessage);
            var downloadPath = file.Path.LocalPath;
                
            while (!validFilename)
            {
                await _dialogService.ShowAlertAsync($"The filename \"{filename}\" is invalid: {errorMessage} Please rename the file and try again.");
                    
                var log = new Message($"Invalid filename \"{filename}\": {errorMessage}", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                    
                options = new FilePickerSaveOptions()
                {
                    SuggestedStartLocation = folder,
                    SuggestedFileName = filename,
                };
                    
                file = await storageService.SaveFilePickerAsync(options);

                if (file == null)
                { 
                    return;
                }
                    
                filename = file.Name.Substring(0, file.Name.LastIndexOf('.'));
                validFilename = DownloadedMedia.TryValidateFileName(filename, out errorMessage); 
                downloadPath = file.Path.LocalPath;
            }
            
            var requestData = new DownloadRequestData()
            {
                Provider = SelectedProvider,
                Urls = new List<string>([Url]),
                Filenames = new List<string>([Filename]),
                PreferredFile = SelectedMediaType.Trim('.') == "auto" ? "" : SelectedMediaType.Trim('.'),
                PreferredType = AppData.ValidMediaTypes[SelectedMediaType],
                DownloadStrategy = "stream",
                AutoConvert = AutoConvert
            };
            var result = await client.SendScrapRequest(requestData);

            foreach (var resource in result.Resources)
            { 
                if (result.TaskId != "-1")
                {
                    Task.Delay(2000).Wait();


                    var progressWindow = new ProgressBarWindow()
                    {
                        OnCancel = () =>
                        {
                            _cts.Cancel();
                        }
                    };
                    progressWindow.Show();

                    var path = downloadPath.Substring(0, downloadPath.LastIndexOf(@"\"));
                    _path = path + @"\" + requestData.Filenames[0] + "." + resource.Context.MediaInfo.FileExtension;

                    string finalPath = "";
                    if (progressWindow.DataContext is ProgressBarWindowViewModel vm)
                        finalPath = await vm.StartProgress(resource,
                            client.GetFileFromStream(resource, path, _cts.Token), _cts);

                    if (!string.IsNullOrEmpty(finalPath) && File.Exists(finalPath))
                    {
                        Task.Delay(1000).Wait();

                        bool isPlayable = false;

                        int maxTries = 10;
                        while (!isPlayable && maxTries > 0)
                        {
                            isPlayable = File.Exists(finalPath);
                            maxTries--;
                        }

                        var req = new CreateDownloadedMediaRequest
                        {
                            UserIdentifier = AppData.CurrentUser.Identifier,
                            DownloadPath = finalPath,
                            DownloadedAt = DateTime.Now.ToString("o"),
                            MediaType = finalPath.Substring(finalPath.LastIndexOf('.')),
                            IsPlayable = isPlayable,
                            Url = Url,
                            Title = Filename
                        };

                        var media = await Database.CreateDownloadedMediaAsync(req);

                        AppData.AddDownloadedMedia(media);
                    }
                    else
                    { 
                        await _dialogService.ShowAlertAsync("An error occurred while downloading the media. Please try again.");
                    } 
                }
            }
            
            RequestClose?.Invoke();
        }
        catch (OperationCanceledException o)
        {
            CancelDownload();
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while scraping the media: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            await _dialogService.ShowAlertAsync("An error occurred while scraping the media: " + ex.Message);
        }
    }

    /// <summary>
    /// Constructor for the SunoScrapWindowViewModel class, which initializes the view model for the Suno scrap window.
    /// It sets up the necessary properties and commands for the scrap functionality, including the CancelCommand that allows the user to close the scrap window without initiating the scrap process.
    /// </summary>
    /// <param name="dialogService"></param>
    public ScrapWindowWithoutSearchViewModel(DialogService dialogService, Window window)
    {
        if (Design.IsDesignMode) return;
        
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
        _dialogService = dialogService;
        _scrapWindow = window;
    }
    
    private void CancelDownload()
    {
        var log = new Message("Scrap operation was canceled by the user.", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        if (!string.IsNullOrEmpty(_path))
        {
            if (File.Exists(_path))
            {
                try
                {
                    File.Delete(_path);
                    var logDelete = new Message($"Partially downloaded file \"{_path}\" was deleted after cancellation.", DateTime.Now, "INFO");
                    _logger.LogNewMassage(logDelete);
                }
                catch (Exception ex)
                {
                    var logError = new Message($"Failed to delete partially downloaded file \"{_path}\": {ex.Message}", DateTime.Now, "ERROR");
                    _logger.LogNewMassage(logError);
                }
            }
            else
            {
                var path = _path.Substring(0, _path.LastIndexOf('.'));
                path += SelectedMediaType;
                
                if (File.Exists(path))
                { 
                    try
                    {
                        File.Delete(path);
                        var logDelete = new Message($"Partially downloaded file \"{path}\" was deleted after cancellation.", DateTime.Now, "INFO");
                        _logger.LogNewMassage(logDelete);
                    }
                    catch (Exception ex)
                    {
                        var logError = new Message($"Failed to delete partially downloaded file \"{path}\": {ex.Message}", DateTime.Now, "ERROR");
                        _logger.LogNewMassage(logError);
                    }
                }
                else
                {
                    _logger.LogNewMassage(new Message($"No partially downloaded file found to delete at \"{_path}\" or \"{path}\" after cancellation.", DateTime.Now, "INFO"));
                }
            }
        }
        else
        {
            _logger.LogNewMassage(new Message($"Path is empty or null check: {_path}", DateTime.Now, "INFO"));
        }
        
        RequestClose?.Invoke();
    }
}