using System.Text.Json.Serialization;

namespace PyScrapperDesktopApp.Models;

public class DownloadRequestData
{
    [JsonPropertyName("provider")]
    public string Provider { get; set; }
        
    [JsonPropertyName("url")]
    public string Url { get; set; }
        
    [JsonPropertyName("mediatype")]
    public string Mediatype { get; set; }
        
    [JsonPropertyName("filename")]
    public string Filename { get; set; }
        
    [JsonPropertyName("download_path")]
    public string Download_path { get; set; }
}


    
public class SearchRequestData
{
    [JsonPropertyName("provider")]
    public string Provider { get; set; }
        
    [JsonPropertyName("search")]
    public string Search { get; set; }
        
    [JsonPropertyName("top")]
    public int Top { get; set; }
}