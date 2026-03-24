using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;

namespace PyScrapperDesktopApp.Models;

public class AppData
{
    public static ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static ObservableCollection<DownloadedMedia> PlayableMedias = new();
    public static ObservableCollection<Playlist> Playlists = new();
    public static string PyScrapperPath { get;} = Directory.GetParent(Directory.GetCurrentDirectory())!.Parent!.Parent!.Parent!.FullName;
    public static string DownloadPath { get;} = Path.Combine(PyScrapperPath, "Downloads");
    public static string AppLogsPath { get;} = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "logs");
    public static string ServerLogsPath { get;} = Path.Combine(PyScrapperPath, "LocalServer", "logs");
    public static string DataPath { get;} = Path.Combine(PyScrapperPath, "PyScrapperDesktopApp", "data");
    
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
    
    public static void AddPlaylist(Playlist playlist)
    {
        Playlists.Add(playlist);
    }

    public static void RemovePlaylist(Playlist playlist)
    {
        Playlists.Remove(playlist);
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
    public int Count => MediaIds.Count;
    
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
}