using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using CommunityToolkit.Mvvm.ComponentModel;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Static class that holds the main data collections and settings for the application, including downloaded media, playable media, playlists, file paths, and application settings.
/// It also provides methods for adding and removing media and playlists, as well as checking for existing media items.
/// </summary>
public static class AppData
{
    public static readonly ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static readonly ObservableCollection<DownloadedMedia> PlayableMedias = new();
    public static readonly ObservableCollection<Playlist> Playlists = new();
    public static string PyScrapperPath { get;} = Directory.GetParent(Directory.GetCurrentDirectory())!.Parent!.Parent!.Parent!.FullName;
    public static string AppLogsPath { get; set; } = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "logs");
    public static string ServerLogsPath { get; set; } = Path.Combine(PyScrapperPath, "LocalServer", "logs");
    public static string DataPath { get; set; } =  Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "data");
    public static Settings Settings = new();
    public static List<string> FileTypes = ["*.mp3", "*.mp4", "*.wav"];
    
    
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
public class DownloadedMedia(string url, string mediaType, DateTime downloadedAt, string downloadPath, bool isPlayable, string identifier)
{
    public int Id { get; set; }
    public string Identifier { get; set; } = identifier;
    public string Title { get; set; } = string.Empty;
    public string Url { get; set; } = url;
    public string MediaType { get; set; } = mediaType;
    public DateTime DownloadedAt { get; set; } = downloadedAt;
    public string DownloadPath { get; set; } = downloadPath;
    public bool IsPlayable { get; set; } = isPlayable;

    private static readonly AppLogger _logger = new();
    
    /// <summary>
    /// Sets the id property to the highest existing id in the provided collection of downloaded medias plus one, ensuring a unique identifier for each media item.
    /// </summary>
    /// <param name="medias"></param>
    public void SetHighestId(ObservableCollection<DownloadedMedia> medias)
    {
        if (medias.Count > 0)
        {
            Id = medias.Max(m => m.Id) + 1;
        }
        else
        {
            Id = 1;
        }
    }

    /// <summary>
    /// Sets the title property of the media item to the file name without the extension from the download path, providing a user-friendly name for the media item based on its file name.
    /// </summary>
    public void SetTitle()
    {
        Title = Path.GetFileNameWithoutExtension(DownloadPath);
    }
}

/// <summary>
/// Class representing a playlist, which contains a list of media IDs and a name, along with a unique identifier for the playlist itself.
/// </summary>
/// <param name="mediaIds"></param>
/// <param name="name"></param>
public class Playlist(List<int> mediaIds, string name, string description)
{
    public int Id { get; set; }
    public string Name { get; set; } = name;
    public string? Description { get; set; } = description;
    public List<int> MediaIds { get; set; } = mediaIds;
    public List<int> PlayableMediaIds { get; set; } = new();
    public int Count { get; set; } = mediaIds.Count;
    
    /// <summary>
    /// Sets the id property to the highest existing id in the provided collection of playlists plus one, ensuring a unique identifier for each playlist item.
    /// </summary>
    /// <param name="playlists"></param>
    public void SetHighestId(ObservableCollection<Playlist> playlists)
    {
        if (playlists.Count > 0)
        {
            Id = playlists.Max(p => p.Id) + 1;
        }
        else
        {
            Id = 1;
        }
    }
    
    /// <summary>
    /// Populates the PlayableMediaIds list with the IDs of media items that are both in the MediaIds list and in the provided collection of playable media items.
    /// </summary>
    /// <param name="playableMedias"></param>
    public void SetPlayableMediaIds(ObservableCollection<DownloadedMedia> playableMedias)
    {
        foreach (var mediaId in MediaIds)
        {
            var media = playableMedias.FirstOrDefault(m => m.Id == mediaId);

            if (media is not null)
            {
                PlayableMediaIds.Add(media.Id);
            }
        }
    }
    
    /// <summary>
    /// Adds a media ID to the MediaIds list if it is not already present, and updates the Count property accordingly.
    /// It also ensures that the playlist is updated in the Playlists collection to reflect the changes.
    /// </summary>
    /// <param name="mediaId"></param>
    public void AddMedia(int mediaId)
    {
        if (!MediaIds.Contains(mediaId))
        {
            var index = AppData.Playlists.IndexOf(this);
            
            MediaIds.Add(mediaId);
            Count = MediaIds.Count;
            
            AppData.Playlists.Insert(index, this);
            AppData.Playlists.RemoveAt(index+1);
        }
    }
    
    /// <summary>
    /// Removes a media ID from the MediaIds list if it is present, and updates the Count property accordingly.
    /// It also ensures that the playlist is updated in the Playlists collection to reflect the changes.
    /// Removing a media ID from the playlist will disassociate that media item from the playlist, but it will not delete the media item itself from the DownloadedMedias collection, allowing the user to maintain their downloaded media while managing their playlists effectively.
    /// </summary>
    /// <param name="mediaId"></param>
    public void RemoveMedia(int mediaId)
    {
        if (MediaIds.Contains(mediaId))
        {
            var index = AppData.Playlists.IndexOf(this);
            
            MediaIds.Remove(mediaId);
            Count = MediaIds.Count;
            
            AppData.Playlists.Insert(index, this);
            AppData.Playlists.RemoveAt(index+1);
        }
    }
}

/// <summary>
/// Class representing the application settings, which includes properties for the download path and server URL, as well as a method to set default settings for the application.
/// </summary>
public class Settings
{
    public int Id = 1;
    public string? DownloadPath { get; set; }
    public string ServerUrl => "http://127.0.0.1:8765";
    public void SetDefaultSettings()
    {
        DownloadPath = Path.Combine(AppData.PyScrapperPath, "Downloads");
    }
}