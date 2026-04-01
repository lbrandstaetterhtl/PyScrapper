using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Interactivity;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// Class responsible for managing the state and logic of the MainWindow, which serves as the central hub of the application. It handles the display of downloaded media, navigation to various functionalities such as scraping from different providers, opening a media player, and viewing logs.
/// The class also manages user interactions through commands and ensures that the UI is updated accordingly based on the application's state and user actions.
/// </summary>
public partial class MainWindowViewModel : ObservableObject
{
    public ObservableCollection<DownloadedMedia> DownloadedMediaList => AppData.DownloadedMedias;
    
    public ObservableCollection<Playlist> Playlists => AppData.Playlists;
    private readonly Window _window;

    /// <summary>
    /// Constructor for the MainWindowViewModel, which initializes the view model and sets up the list of downloaded media by fetching it from the AppData.
    /// It also checks if the application is in design mode to avoid executing code that should only run at runtime.
    /// </summary>
    public MainWindowViewModel(Window window)
    {
        if (Design.IsDesignMode) return;
        _window = window;
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to open the Suno scrap window.
    /// It checks if the application is running in a desktop environment and then creates and shows the SunoScrapWindow as a dialog, allowing the user to interact with it without leaving the main window.
    /// </summary>
    [RelayCommand]
    private async Task OpenSunoScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var sunoScrapWindow = new Views.SunoScrapWindow();
        await sunoScrapWindow.ShowDialog(desktop.MainWindow);
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to check the server health.
    /// It creates and shows the GetServerHealthWindow, which displays the health status of the server by periodically fetching data from an API endpoint.
    /// This allows the user to monitor the server's status
    /// </summary>
    [RelayCommand]
    private void GetHealth()
    {
        if (Design.IsDesignMode) return;
        
        var getHealthWindow = new GetServerHealthWindow();
        getHealthWindow.Show();
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to open the media player window.
    /// It prompts the user to enter a valid file path for an audio file (e.g., .mp3) and checks if the file exists. If the file exists, it creates and shows the MediaPlayerWindow, allowing the user to play the selected media file.
    /// If the file does not exist, it displays a message box informing the user to check the path and try again.
    /// This functionality enables the user to easily access and play their media files directly from the main window of the application.
    /// </summary>
    [RelayCommand]
    private async Task OpenMediaPlayerWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;

        var path = await new InputWindow("Enter a valid file path (.mp3)").ShowDialog<string>(desktop.MainWindow);

        if (path == null)
        {
            return;
        }
        
        if (!File.Exists(path))
        {
            var messageBox = new MessageBox("File does not exist. Please check the path and try again.");
            await messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
        
        string mediaType = Path.GetExtension(path);
        
        var guid = Guid.NewGuid().ToString();
        var media = new DownloadedMedia("N/A", mediaType, DateTime.Now, path, true, guid);
        media.SetTitle();
        media.SetHighestId(AppData.DownloadedMedias);
        AppData.AddDownloadedMedia(media);

        List<int> mediaIds = [media.Id];

        var playlist = new Playlist(mediaIds, "NPLL", "");
        
        var mediaPlayerWindow = new MediaPlayerWindow(playlist);
        mediaPlayerWindow.Show();
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to open the YouTube scrap window.
    /// It checks if the application is running in a desktop environment and then creates and shows the ScrapWindowWithSearch with "youtube" as the provider, allowing the user to interact with it and perform scraping operations specific to YouTube without leaving the main window.
    /// </summary>
    [RelayCommand]
    private async Task OpenYoutubeScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var youtubeScrapWindow = new ScrapWindowWithSearch("youtube");
        await youtubeScrapWindow.ShowDialog(desktop.MainWindow);
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to open the Bandcamp scrap window.
    /// It checks if the application is running in a desktop environment and then creates and shows the ScrapWindowWithSearch with "bandcamp" as the provider, allowing the user to interact with it and perform scraping operations specific to Bandcamp without leaving the main window.
    /// </summary>
    [RelayCommand]
    private async Task OpenBandcampScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;

        var bandcampScrapWindow = new ScrapWindowWithSearch("bandcamp");
        await bandcampScrapWindow.ShowDialog(desktop.MainWindow);
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to show the application logs.
    /// It reads the contents of the app.log file from the application's logs directory and displays it in a new LogsWindow.
    /// If the log file does not exist, it shows a message indicating that no logs were found.
    /// This allows the user to easily access and review the application logs for troubleshooting or monitoring purposes directly from the main window.
    /// </summary>
    [RelayCommand]
    private void ShowAppLogs()
    {
        var logs = File.Exists(AppData.AppLogsPath + @"\app.log") ? File.ReadAllText(AppData.AppLogsPath + @"\app.log") : "No logs found.";
        var label = "App Logs:\n\n";
        
        var logWindow = new LogsWindow(logs, label);
        logWindow.Show();
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to show the server logs.
    /// It reads the contents of the server_runtime.log file from the application's server logs directory and displays it in a new LogsWindow.
    /// If the log file does not exist, it shows a message indicating that no logs were found.
    /// This allows the user to easily access and review the server logs for troubleshooting or monitoring purposes directly from the main window, providing insights into the server's runtime behavior and any potential issues that may arise.
    /// </summary>
    [RelayCommand]
    private void ShowServerLogs()
    {
        var logs = File.Exists(AppData.ServerLogsPath + @"\server_runtime.log") ? File.ReadAllText(AppData.ServerLogsPath + @"\server_runtime.log") : "No logs found.";
        var label = "Server Logs:\n\n";
        
        var logWindow = new LogsWindow(logs, label);
        logWindow.Show();
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to create a new playlist.
    /// It checks if the application is running in a desktop environment and then creates and shows the CreatePlaylistWindow as a dialog, allowing the user to interact with it and create a new playlist without leaving the main window.
    /// This functionality enables users to easily manage their playlists directly from the main window of the application, enhancing the overall user experience and providing convenient access to playlist creation features.
    /// </summary>
    [RelayCommand]
    private void CreatePlaylist()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;

        var createPlaylistWindow = new CreatePlaylistWindow();
        createPlaylistWindow.ShowDialog(desktop.MainWindow);
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to sort the downloaded media by name.
    /// It sorts the DownloadedMedias collection in AppData by the Title property of each media item, clears the existing collection, and then repopulates it with the sorted list.
    /// This allows the user to easily organize and view their downloaded media in alphabetical order based on the media titles, enhancing the usability and navigation of the media library within the application.
    /// </summary>
    [RelayCommand]
    private void SortByName()
    {
        var sortedList = AppData.DownloadedMedias.OrderBy(m => m.Title).ToList();
        AppData.DownloadedMedias.Clear();
        foreach (var media in sortedList)
        {
            AppData.DownloadedMedias.Add(media);
        }
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to sort the downloaded media by date.
    /// It sorts the DownloadedMedias collection in AppData by the DownloadedAt property of each media item, clears the existing collection, and then repopulates it with the sorted list.
    /// This allows the user to easily organize and view their downloaded media in chronological order based on the date they were downloaded, enhancing the usability and navigation of the media library within the application by providing a clear timeline of when each media item was added to the collection.
    /// </summary>
    [RelayCommand]
    private void SortByDate()
    {
        var sortedList = AppData.DownloadedMedias.OrderBy(m => m.DownloadedAt).ToList();
        AppData.DownloadedMedias.Clear();
        foreach (var media in sortedList)
        {
            AppData.DownloadedMedias.Add(media);
        }
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to sort the downloaded media by ID.
    /// It sorts the DownloadedMedias collection in AppData by the Id property of each media item, clears the existing collection, and then repopulates it with the sorted list.
    /// This allows the user to easily organize and view their downloaded media in order of their unique identifiers, which can be useful for tracking and managing media items based on their assigned IDs within the application.
    /// Sorting by ID can provide a consistent and straightforward way to view media items in the order they were added to the collection, especially if the IDs are assigned sequentially as new media items are added.
    /// </summary>
    [RelayCommand]
    private void SortById()
    {
        var sortedList = AppData.DownloadedMedias.OrderBy(m => m.Id).ToList();
        AppData.DownloadedMedias.Clear();
        foreach (var media in sortedList)
        {
            AppData.DownloadedMedias.Add(media);
        }
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to convert a media file to a supported codec (e.g., H264).
    /// It prompts the user to enter a file path for the media file they want to convert, checks if the file exists, and then asks for confirmation to proceed with the conversion.
    /// </summary>
    [RelayCommand]
    private async Task ConvertCodec()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var inputWindow = new InputWindow("Enter a file to convert:");
        var inputPath = await inputWindow.ShowDialog<string>(desktop.MainWindow);
        
        if (inputPath == null)
        {
            return;
        }
        
        if (!File.Exists(inputPath))
        {
            var messageBox = new MessageBox("File does not exist. Please check the path and try again.");
            await messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
        
        var message = "Would you like to convert it to a supported codec H264?";
        var confirmationWindow = new ConfirmationWindow(message);
        var confirmationResult = await confirmationWindow.ShowDialog<bool>(desktop.MainWindow);

        if (!confirmationResult)
            return;
        
        var outputPath = CodecConverterWindowViewModel.SetOutputPath(inputPath);
        var codecConverterWindow = new CodecConverterWindow(inputPath: inputPath, outputPath: outputPath);
        bool finished = await codecConverterWindow.ShowDialog<bool>(desktop.MainWindow);

        if (!finished)
        {
            var log = new Massage($"Codec conversion for file '{inputPath}' was cancelled by user.", DateTime.Now, "WARNING");
            new AppLogger().LogNewMassage(log);
        }
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to scan a folder for media files.
    /// It prompts the user to enter a folder path, and then calls the App.ScanFolder method with the provided path to scan for media files within that folder.
    /// </summary>
    [RelayCommand]
    private async Task ScanFolder()
    {
        try
        {
            var topLevel = TopLevel.GetTopLevel(_window);
            var storageService = new StorageService(topLevel!);
            var folders = await storageService.OpenFolderPickerAsync(new FolderPickerOpenOptions()
            {
                Title = "Select a folder",
                AllowMultiple = false
            });

            if (folders.Count > 0)
            {
                string folderPath = folders[0].TryGetLocalPath() ??
                                    throw new InvalidOperationException(
                                        "Unable to get local path of the selected folder.");
                App.ScanFolder(folderPath);
            }
        }
        catch (Exception ex)
        {
            var log = new Massage($"Error while scanning folder: {ex.Message}", DateTime.Now, "ERROR");
            new AppLogger().LogNewMassage(log);
            var messageBox = new MessageBox($"Error while scanning folder: {ex.Message}");
            await messageBox.ShowDialog(App.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
        }
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the button to delete all downloaded media from the list.
    /// It prompts the user with a confirmation dialog to ensure they want to proceed with deleting all media items, as this action cannot be undone.
    /// If the user confirms, it clears the DownloadedMedias collection in AppData, effectively removing all media items from the list and allowing the user to start fresh with a new set of downloaded media.
    /// This functionality provides a convenient way for users to manage their media library and maintain a clean slate when needed, while also ensuring that they are aware of the consequences of their action through the confirmation dialog.
    /// </summary>
    [RelayCommand]
    private async Task DeleteAllMedias()
    {
        var confirmationWindow = new ConfirmationWindow("Are you sure you want to delete all downloaded media? This action cannot be undone.");
        var result = await confirmationWindow.ShowDialog<bool>(App.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);

        if (!result)
            return;
        
        AppData.DownloadedMedias.Clear();
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to delete all playlists from the list.
    /// It prompts the user with a confirmation dialog to ensure they want to proceed with deleting all playlists, as this action cannot be undone.
    /// If the user confirms, it clears the Playlists collection in AppData, effectively removing all playlists from the list and allowing the user to start fresh with a new set of playlists.
    /// This functionality provides a convenient way for users to manage their playlists and maintain a clean slate when needed, while also ensuring that they are aware of the consequences of their action through the confirmation dialog.
    /// </summary>
    [RelayCommand]
    private async Task DeleteAllPlaylists()
    {
        var confirmationWindow = new ConfirmationWindow("Are you sure you want to delete all playlists? This action cannot be undone.");
        var result = await confirmationWindow.ShowDialog<bool>(App.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);

        if (!result)
            return;
        
        AppData.Playlists.Clear();
    }

    /// <summary>
    /// Command method that is executed when the user clicks the button to edit the default download path for media files.
    /// It prompts the user to enter a new download path, displaying the current path for reference.
    /// If the user provides a new path, it checks if the path is valid (i.e., it exists and is not empty).
    /// If the path is valid, it updates the DownloadPath property in AppData.Settings with the new path.
    /// If the path is invalid, it shows a message box informing the user to select a valid download path and try again.
    /// This functionality allows users to customize where their downloaded media files are stored, providing flexibility and control over their file organization while ensuring that the application can access the specified location for saving media files.
    /// </summary>
    [RelayCommand]
    private async Task EditDownloadsPath()
    {
        if (App.Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop) return;
        
        var inputWindow = new InputWindow($"Set a new default download path (Current: {AppData.Settings.DownloadPath}):");
        var input = await inputWindow.ShowDialog<string>(desktop.MainWindow);
        
        if (input == null)
        {
            return;
        }

        if (!Directory.Exists(input) || string.IsNullOrWhiteSpace(input))
        {
            var messageBox = new MessageBox("Please select a valid download path.");
            await messageBox.ShowDialog(desktop.MainWindow);
            return;
        }
        
        AppData.Settings.DownloadPath = input;
    }

    [RelayCommand]
    private void ToggleTheme()
    {
        App.ToggleTheme();
    }
}