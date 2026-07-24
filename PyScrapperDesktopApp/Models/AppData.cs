using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using DotNetEnv;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Static class that holds the main data collections and settings for the application, including downloaded media, playable media, playlists, file paths, and application settings.
/// It also provides methods for adding and removing media and playlists, as well as checking for existing media items.
/// </summary>
public class AppData : Interfaces.IAppDataService 
{
    ObservableCollection<DownloadedMedia> Interfaces.IAppDataService.DownloadedMedias => DownloadedMedias;
    ObservableCollection<Playlist> Interfaces.IAppDataService.Playlists => Playlists;
    Settings Interfaces.IAppDataService.Settings => Settings;
    

    void Interfaces.IAppDataService.AddDownloadedMedia(DownloadedMedia media) => AddDownloadedMedia(media);
    void Interfaces.IAppDataService.RemoveDownloadedMedia(DownloadedMedia media) => RemoveDownloadedMedia(media);
    bool Interfaces.IAppDataService.MediaAlreadyExists(string filePath) => MediaAlreadyExists(filePath);

    public static readonly ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static MediaFilter CurrentMediaFilter = new();
    public static List<DownloadedMedia> OriginalDownloadedMedias = new();
    public static readonly ObservableCollection<DownloadedMedia> PlayableMedias = new();
    public static bool FilterEnabled = false;
    public static readonly ObservableCollection<Playlist> Playlists = new();
    public static User CurrentUser = null;
    public static Settings Settings = new("default");
    public static List<PlaylistMedia> PlaylistMedias = new();
    public static string AdminKey;
    public static string PyScrapperPath { get;} = Directory.GetParent(Directory.GetCurrentDirectory())!.Parent!.Parent!.Parent!.FullName;
    public static string AppLogsPath { get; set; } = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "logs");
    public static string ServerLogsPath { get; set; } = Path.Combine(PyScrapperPath, "LocalServer", "logs");
    public static string DataPath { get; set; } =  Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "data");
    public static string AssetPath { get; set; } = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "Assets");
    public static readonly List<FilePickerFileType> FileTypes = 
    [
        new ("Media Files") 
        { 
            Patterns = ["*.mp4", "*.mp3", "*.wav"] 
        },
        new ("Video Files")
        {
            Patterns = ["*.mp4"] 
        }
    ];

    public static List<string> ValidMediaTypes = [".mp3", ".mp4"];
    public static List<string> ValidProviders = ["suno", "youtube", "bandcamp", "archive"];
    
    static AppData()
    {
        var envPath = Path.Combine(PyScrapperPath, ".env");
        Console.WriteLine($"Looking for .env at: {envPath}");
        Console.WriteLine($"File exists: {File.Exists(envPath)}");
        Env.Load(Path.Combine(PyScrapperPath, ".env"));
        AdminKey = Environment.GetEnvironmentVariable("ADMIN_KEY") ?? throw new Exception("ADMIN_KEY not found in .env file.");
    }
    
    /// <summary>
    /// Adds a downloaded media to the DownloadedMedias collection and, if it's playable, also to the PlayableMedias collection.
    /// </summary>
    /// <param name="media"></param>
    public static void AddDownloadedMedia(DownloadedMedia media)
    {
        DownloadedMedias.Add(media);
        
        if (media.IsPlayable)
        {
            PlayableMedias.Add(media);
        }
    }
    
    /// <summary>
    /// Removes a downloaded media from the DownloadedMedias collection and, if it's playable, also from the PlayableMedias collection.
    /// </summary>
    /// <param name="media"></param>
    public static void RemoveDownloadedMedia(DownloadedMedia media)
    {
        DownloadedMedias.Remove(media);
        
        if (media.IsPlayable)
        {
            PlayableMedias.Remove(media);
        }
    }

    /// <summary>
    /// Adds a playlist to the Playlists collection.
    /// This method allows the application to manage and organize playlists created by the user, enabling them to group media items together for easier access and playback.
    /// </summary>
    /// <param name="playlist"></param>
    public static void AddPlaylist(Playlist playlist)
    {
        Playlists.Add(playlist);
    }

    /// <summary>
    /// Removes a playlist from the Playlists collection.
    /// This method allows the application to manage and organize playlists created by the user, enabling them to group media items together for easier access and playback. Removing a playlist will delete the association of the media items within that playlist, but it will not delete the media items themselves from the DownloadedMedias collection, allowing the user to maintain their downloaded media while managing their playlists effectively.
    /// </summary>
    /// <param name="playlist"></param>
    public static void RemovePlaylist(Playlist playlist)
    {
        Playlists.Remove(playlist);
    }

    /// <summary>
    /// Checks if a media item with the specified file path already exists in the DownloadedMedias collection.
    /// This method is useful for preventing duplicate entries in the media library and ensuring that each downloaded media item is unique based on its file path.
    /// It returns true if a media item with the given file path is found, and false otherwise.
    /// </summary>
    /// <param name="filePath"></param>
    /// <returns></returns>
    public static bool MediaAlreadyExists(string filePath)
    {
        return DownloadedMedias.Any(m => m.DownloadPath == filePath);
    }
}

/// <summary>
/// Class representing a media item that has been downloaded, with properties for URL, media type, download time, file path, playability, and a unique identifier.
/// </summary>
/// <param name="url"></param>
/// <param name="mediaType"></param>
/// <param name="downloadedAt"></param>
/// <param name="downloadPath"></param>
/// <param name="isPlayable"></param>
/// <param name="identifier"></param>
public partial class DownloadedMedia(string userIdentifier, string title, string url, string mediaType, DateTime downloadedAt, string downloadPath, bool isPlayable, string identifier) : ObservableObject
{
    [ObservableProperty]
    private string _identifier = identifier;
    
    [ObservableProperty]
    private string _userIdentifier = userIdentifier;

    [ObservableProperty] 
    private string _title = title;
    
    [ObservableProperty]
    private string _url = url;
    
    [ObservableProperty]
    private string _mediaType = mediaType;
    
    [ObservableProperty]
    private DateTime _downloadedAt = downloadedAt;
    
    [ObservableProperty]
    private string _downloadPath = downloadPath;

    [ObservableProperty]
    private bool _isPlayable = isPlayable;

    private static readonly AppLogger _logger = new();
    
    
     private static readonly HashSet<string> ReservedWindowsNames = new(StringComparer.OrdinalIgnoreCase)
        {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        };
    
        /// <summary>
        /// Tries to validate the provided file name by checking if it is not empty, does not end with a space or dot, does not contain invalid characters, and is not a reserved Windows name.
        /// If the file name is valid, it returns true; otherwise, it returns false and provides an appropriate error message indicating the reason for the validation failure.
        /// </summary>
        /// <param name="fileName"></param>
        /// <param name="errorMessage"></param>
        /// <returns></returns>
        public static bool TryValidateFileName(string? fileName, out string errorMessage)
        {
            errorMessage = string.Empty;
    
            if (string.IsNullOrWhiteSpace(fileName))
            {
                errorMessage = "Filename must not be empty.";
                return false;
            }
    
            fileName = fileName.Trim();
    
            if (fileName.EndsWith(' ') || fileName.EndsWith('.'))
            {
                errorMessage = "Filename must not end with a space or dot.";
                return false;
            }
    
            if (fileName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0)
            {
                errorMessage = "Filename contains invalid characters.";
                return false;
            }
    
            if (ReservedWindowsNames.Contains(fileName))
            {
                errorMessage = "Filename is a reserved Windows name.";
                return false;
            }
    
            return true;
        }
}

/// <summary>
/// Class representing a playlist, which contains a list of media IDs and a name, along with a unique identifier for the playlist itself.
/// </summary>
/// <param name="mediaIds"></param>
/// <param name="name"></param>
public class Playlist(string name, string description, string identifier, string userIdentifier)
{
    public string Identifier { get; set; } = identifier;
    public string UserIdentifier { get; set; } = userIdentifier;
    public string Name { get; set; } = name;
    public string? Description { get; set; } = description;
    public List<string> MediaIdentifiers { get; set; } = new();
    
    public async Task AddNewMedia(string mediaIdentifier)
    {
        if (!AppData.PlaylistMedias.Any(pm => pm.MediaIdentifier == mediaIdentifier && pm.PlaylistIdentifier == Identifier))
        {
            var req = new CreatePlaylistMediaRequest
            {
                PlaylistIdentifier = Identifier,
                MediaIdentifier = mediaIdentifier
            };

            var playlistMedia = await Database.CreatePlaylistMedia(req);
            AppData.PlaylistMedias.Add(playlistMedia);
        }
    }

    public void FindMedias()
    {
        var medias = AppData.PlaylistMedias.Where(pm => pm.PlaylistIdentifier == Identifier).ToList();
        MediaIdentifiers = medias.Select(pm => pm.MediaIdentifier).ToList();
    }
    
    public void RemoveMedia(string mediaIdentifier)
    {
        var playlistMedia = AppData.PlaylistMedias.FirstOrDefault(pm => pm.MediaIdentifier == mediaIdentifier && pm.PlaylistIdentifier == Identifier);
        if (playlistMedia != null)
        {
            AppData.PlaylistMedias.Remove(playlistMedia);
        }
    }
}

/// <summary>
/// Class representing the application settings, which includes properties for the download path and server URL, as well as a method to set default settings for the application.
/// </summary>
public class Settings(string identifier)
{
    public string Identifier { get; set; } = identifier;
    public string? DownloadPath { get; set; }
    public string ServerUrl
    {
        get => "http://127.0.0.1:8765";
    }

    public bool DarkModeEnabled { get; set; }
    public bool ScanFolderOnStartup { get; set; }
    public void SetDefaultSettings()
    {
        DownloadPath = Path.Combine(AppData.PyScrapperPath, "Downloads");
        DarkModeEnabled = true;
        ScanFolderOnStartup = false;
    }
}

/// <summary>
/// Class representing a media filter, which contains properties for search query, media types, date range, and playability.
/// It also includes static methods to apply the filter to the downloaded media collection and to clear the filter,
/// allowing users to easily manage and organize their media library based on specific criteria such as search terms, media types, download dates, and playability status.
/// </summary>
public class MediaFilter
{
    public string? SearchQuery { get; set; } = null;
    
    public ObservableCollection<string>? MediaTypes { get; set; } = null;

    public DateTimeOffset? StartDate { get; set; } = null;
    public DateTimeOffset? EndDate { get; set; } = null;
    
    public bool IsPlayable { get; set; } = false;
    
    private static readonly AppLogger _logger = new();

    /// <summary>
    /// Applies the provided media filter to the DownloadedMedias collection, filtering the media items based on the specified criteria such as search query, media types, date range, and playability status.
    /// It updates the DownloadedMedias collection to only include media items that match the filter criteria, allowing users to easily manage and organize their media library based on specific preferences.
    /// If an error occurs during the filtering process, it logs the error and displays a message box to inform the user of the issue.
    /// </summary>
    /// <param name="filter"></param>
    public static async Task ApplyMediaFilter(MediaFilter filter)
    {
        try
        {
            if (AppData.FilterEnabled)
            {
                
            }

            AppData.FilterEnabled = true;
            AppData.CurrentMediaFilter = filter;
            AppData.OriginalDownloadedMedias = AppData.DownloadedMedias.ToList();
            AppData.DownloadedMedias.Clear();

            foreach (var media in AppData.OriginalDownloadedMedias)
            {
                bool matches =
                    (filter.SearchQuery == null || media.Title.Contains(filter.SearchQuery, StringComparison.OrdinalIgnoreCase)) &&
                    (filter.MediaTypes == null || filter.MediaTypes.Contains(media.MediaType)) &&
                    (filter.StartDate == null || media.DownloadedAt >= filter.StartDate.Value.DateTime) &&
                    (filter.EndDate == null || media.DownloadedAt <= filter.EndDate.Value.DateTime) &&
                    (!filter.IsPlayable || media.IsPlayable == filter.IsPlayable);

                if (matches)
                    AppData.AddDownloadedMedia(media);
            }
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while applying the media filter: " + ex.InnerException!.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while applying the media filter: " + ex.Message);
            await messageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
        }
    }
    
    /// <summary>
    /// Clears the currently applied media filter and restores the DownloadedMedias collection to its original state before the filter was applied.
    /// </summary>
    /// <exception cref="Exception"></exception>
    public static async Task ClearFilter()
    {
        try
        {
            if (AppData.FilterEnabled == false)
            {
                throw new Exception("No active filter to clear.", new Exception("No active filter"));
            }

            AppData.FilterEnabled = false;
            AppData.DownloadedMedias.Clear();
            AppData.CurrentMediaFilter = new MediaFilter();

            foreach (var media in AppData.OriginalDownloadedMedias)
            {
                AppData.AddDownloadedMedia(media);
            }

            AppData.OriginalDownloadedMedias.Clear();
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while clearing the filter: " + ex.InnerException!.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var messageBox = new MessageBox("An error occurred while clearing the filter: " + ex.Message);
            await messageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
        }
    }

    /// <summary>
    /// Builds a MediaFilter object based on the provided parameters, allowing users to create a filter with specific criteria such as search query, media types, date range, and playability status.
    /// </summary>
    /// <param name="searchQuery"></param>
    /// <param name="mediaTypes"></param>
    /// <param name="startDate"></param>
    /// <param name="endDate"></param>
    /// <param name="isPlayable"></param>
    /// <returns></returns>
    public static MediaFilter BuildMediaFilter(string? searchQuery, ObservableCollection<string>? mediaTypes, DateTimeOffset? startDate,
        DateTimeOffset? endDate, bool isPlayable)
    {
        MediaFilter filter = new()
        {
            SearchQuery = searchQuery,
            MediaTypes = mediaTypes,
            StartDate = startDate,
            EndDate = endDate,
            IsPlayable = isPlayable
         };
        
        return filter;
    }
}

public class User(string username, string identifier)
{
    public string Username { get; set; } = username;
    public string Identifier { get; set; } = identifier;
}

public class PlaylistMedia(string mediaIdentifier, string playlistIdentifier, int position)
{
    public string MediaIdentifier { get; set; } = mediaIdentifier;
    public string PlaylistIdentifier { get; set; } = playlistIdentifier;
    public int Position { get; set; } = position;
}

public enum LoginResult
{
    Success,
    Cancelled,
    Error
}