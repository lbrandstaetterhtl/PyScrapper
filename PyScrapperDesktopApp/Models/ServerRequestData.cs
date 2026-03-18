using System.Text.Json.Serialization;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Class representing the data structure for a download request, containing properties for the provider, URL, media type, filename, and download path.
/// This class is used to serialize and deserialize JSON data when making download requests to the server.
/// </summary>
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

/// <summary>
/// Class representing the data structure for a search request, containing properties for the provider, search query, and the number of top results to return.
/// This class is used to serialize and deserialize JSON data when making search requests to the server.
/// </summary>
public class SearchRequestData
{
    [JsonPropertyName("provider")]
    public string Provider { get; set; }
        
    [JsonPropertyName("search")]
    public string Search { get; set; }
        
    [JsonPropertyName("top")]
    public int Top { get; set; }
}