using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;

namespace PyScrapperDesktopApp.Models;

public class AppData
{
    public static ObservableCollection<DownloadedMedia> DownloadedMedias = new();
    public static ObservableCollection<DownloadedMedia> PlayableMedias = new();
    public static string PyScrapperPath { get;} = Directory.GetParent(Directory.GetCurrentDirectory())!.Parent!.Parent!.Parent!.FullName;
    public static string DownloadPath { get;} = Path.Combine(PyScrapperPath, "Downloads");
    public static string LogsPath { get;} = Path.Combine(PyScrapperPath + @"\PyScrapperDesktopApp", "logs");
    public static string DataPath { get;} = Path.Combine(PyScrapperPath + @"\PyScrapperDesktopApp", "data");
    
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


public class DownloadedMedia(string url, string mediaType, DateTime downloadedAt, string downloadPath, bool isPlayable, string identifier)
{
    public int Id { get; set; }
    public string Identifier { get; set; } = identifier;
    public string Url { get; set; } = url;
    public string MediaType { get; set; } = mediaType;
    public DateTime DownloadedAt { get; set; } = downloadedAt;
    public string DownloadPath { get; set; } = downloadPath;
    public bool IsPlayable { get; set; } = isPlayable;

    private static readonly AppLogger _logger = new();
    
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
    
    public static ObservableCollection<DownloadedMedia> GetMediasFromJson(string jsonFilePath)
    {
        var log = new Massage($"Loading downloaded medias from {jsonFilePath}", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        if (File.Exists(jsonFilePath))
        {
            var jsonData = File.ReadAllText(jsonFilePath);
            var medias = System.Text.Json.JsonSerializer.Deserialize<ObservableCollection<DownloadedMedia>>(jsonData);
            
            log = new Massage($"Loaded {medias?.Count ?? 0} downloaded medias from {jsonFilePath}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            return medias ?? new ObservableCollection<DownloadedMedia>();
        }
        
        log = new Massage($"No downloaded medias found at {jsonFilePath}, starting with empty collection", DateTime.Now, "WARNING");
        _logger.LogNewMassage(log);
        
        return new ObservableCollection<DownloadedMedia>();
    }
    
    public static void SaveMediasToJson(ObservableCollection<DownloadedMedia> medias, string jsonFilePath)
    {
        try
        {
            var log = new Massage($"Saving {medias.Count} downloaded medias to {jsonFilePath}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (!File.Exists(jsonFilePath) || !Directory.Exists(Path.GetDirectoryName(jsonFilePath)))
            {
                log = new Massage($"Data file {jsonFilePath} does not exist, creating new file and directories",
                    DateTime.Now, "WARNING");
                _logger.LogNewMassage(log);

                Directory.CreateDirectory(Path.GetDirectoryName(jsonFilePath)!);
                File.Create(jsonFilePath).Dispose();
            }

            log = new Massage("Downloaded medias saved successfully", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var jsonData = System.Text.Json.JsonSerializer.Serialize(medias);
            File.WriteAllText(jsonFilePath, jsonData);

        }
        catch (Exception e)
        {
            var log = new Massage($"Error saving downloaded medias to {jsonFilePath}: {e.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }
}