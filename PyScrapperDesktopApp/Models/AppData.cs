using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;

namespace PyScrapperDesktopApp.Models;

public class AppData
{
    public static ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static ObservableCollection<DownloadedMedia> PlayableMedias = new();
    
    public AppData()
    {
        
    }
    
    public static void AddDownloadedMedia(DownloadedMedia media)
    {
        DownloadedMedias.Add(media);
        
        if (media.IsPlayable)
        {
            PlayableMedias.Add(media);
        }
    }
    
    public static void RemoveDownloadedMedia(DownloadedMedia media)
    {
        DownloadedMedias.Remove(media);
        
        if (media.IsPlayable)
        {
            PlayableMedias.Remove(media);
        }
    }
}


public class DownloadedMedia(string url, string mediaType, DateTime downloadedAt, string downloadPath, bool isPlayable)
{
    public int Id { get; set; }
    public string Url { get; set; } = url;
    public string MediaType { get; set; } = mediaType;
    public DateTime DownloadedAt { get; set; } = downloadedAt;
    public string DownloadPath { get; set; } = downloadPath;
    public bool IsPlayable { get; set; } = isPlayable;
    
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
}