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
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

public partial class SunoScrapWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _sunoUrl;
    
    private List<string> _availableMediaType = [".mp3", ".mp4"];

    [ObservableProperty]
    private string _selectedMediaType;
    
    private Window _ScrapWindow;

    [ObservableProperty]
    private string _filename;
    public RelayCommand CancelCommand { get; set; }
    
    public IEnumerable<string> AvailableMediaTypes => _availableMediaType;
    
    public event Action? RequestClose;
    
    [RelayCommand]
    private async Task Scrap()
    {
            ApiClient client = new();
        
            string serverUrl = "127.0.0.1:8765";
        
            var requestData = new DownloadRequestData()
            {
                Provider = "suno",
                Url = SunoUrl,
                Mediatype = SelectedMediaType,
                Filename = Filename,
                Download_path = AppData.DownloadPath
            };
        
            var result = await client.SendScrapRequest(requestData, serverUrl);
        
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
                    var identifier = SunoUrl.Split('/')[^1];

                    var downloadedFilePath = Path.Combine(AppData.DownloadPath, $"{Filename}{SelectedMediaType}");

                    bool isPlayable = File.Exists(downloadedFilePath);

                    var media = new DownloadedMedia(SunoUrl, SelectedMediaType, DateTime.Now, downloadedFilePath,
                        isPlayable, identifier);
                    media.SetHighestId(AppData.DownloadedMedias);

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

    public SunoScrapWindowViewModel(Window scrapWindow)
    {
        if (Design.IsDesignMode) return;
        
        _ScrapWindow = scrapWindow;
        CancelCommand = new RelayCommand(() => RequestClose?.Invoke());
    }
}