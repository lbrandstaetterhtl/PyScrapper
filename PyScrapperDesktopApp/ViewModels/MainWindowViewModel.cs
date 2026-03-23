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

    /// <summary>
    /// Constructor for the MainWindowViewModel, which initializes the view model and sets up the list of downloaded media by fetching it from the AppData.
    /// It also checks if the application is in design mode to avoid executing code that should only run at runtime.
    /// </summary>
    public MainWindowViewModel()
    {
        if (Design.IsDesignMode) return;
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
            
        var mediaPlayerWindow = new MediaPlayerWindow(path);
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
}