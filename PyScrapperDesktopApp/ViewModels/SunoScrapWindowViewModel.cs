using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Xml;
using Avalonia.Controls;
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
public partial class SunoScrapWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _sunoUrl;
    
    private readonly List<string> _availableMediaType = [".mp3", ".mp4"];

    [ObservableProperty]
    private string _selectedMediaType;
    
    private Window _ScrapWindow;

    [ObservableProperty]
    private string _filename;
    public RelayCommand CancelCommand { get; set; }
    
    public IEnumerable<string> AvailableMediaTypes => _availableMediaType;
    
    public event Action? RequestClose;
    
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
            ApiClient client = new();
        
            var requestData = new DownloadRequestData()
            {
                Provider = "suno",
                Url = SunoUrl,
                Mediatype = SelectedMediaType,
                Filename = Filename,
                Download_path = AppData.Settings.DownloadPath
            };
        
            var result = await client.SendScrapRequest(requestData);
        
            if (result != "-1")
            {
                Task.Delay(2000).Wait();
                
                var progressWindow = new ProgressBarWindow();
                progressWindow.Show();

                bool errorWhileDownloading = false;
                if (progressWindow.DataContext is ProgressBarWindowViewModel vm)
                    errorWhileDownloading = await vm.StartProgress(result);

                if (!errorWhileDownloading)
                {
                    Task.Delay(2000).Wait();
                    
                    var identifier = SunoUrl.Split('/')[^1];

                    var downloadedFilePath = Path.Combine(AppData.Settings.DownloadPath, $"{Filename}{SelectedMediaType}");

                    bool isPlayable = File.Exists(downloadedFilePath);

                    var media = new DownloadedMedia(SunoUrl, SelectedMediaType, DateTime.Now, downloadedFilePath,
                        isPlayable, identifier);
                    media.SetHighestId(AppData.DownloadedMedias);
                    media.SetTitle();

                    AppData.AddDownloadedMedia(media);
                }
                else
                {
                    var massageBox = new MessageBox("Download failed, check logs for more details");
                    await massageBox.ShowDialog(_ScrapWindow);
                }
            }
            
            RequestClose?.Invoke();
    }

    /// <summary>
    /// Constructor for the SunoScrapWindowViewModel class, which initializes the view model for the Suno scrap window.
    /// It sets up the necessary properties and commands for the scrap functionality, including the CancelCommand that allows the user to close the scrap window without initiating the scrap process.
    /// </summary>
    /// <param name="scrapWindow"></param>
    public SunoScrapWindowViewModel(Window scrapWindow)
    {
        if (Design.IsDesignMode) return;
        
        _ScrapWindow = scrapWindow;
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
}