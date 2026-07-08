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

public class CreateDownloadedMediaRequest
{
    [JsonPropertyName("UserIdentifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("Url")]
    public string Url { get; set; }
    
    [JsonPropertyName("DownloadPath")]
    public string DownloadPath { get; set; }
    
    [JsonPropertyName("MediaType")]
    public string MediaType { get; set; }
    
    [JsonPropertyName("DownloadedAt")]
    public string DownloadedAt { get; set; }
    
    [JsonPropertyName("IsPlayable")]
    public bool IsPlayable { get; set; }
    
    [JsonPropertyName("Titel")]
    public string Titel { get; set; }
}

public class CreatePlaylistRequest
{
    [JsonPropertyName("UserIdentifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("Name")]
    public string Name { get; set; }
    
    [JsonPropertyName("Description")]
    public string Description { get; set; }
}

public class CreatePlaylistMediaRequest
{
    [JsonPropertyName("PlaylistIdentifier")]
    public string PlaylistIdentifier { get; set; }
    
    [JsonPropertyName("MediaIdentifier")]
    public string MediaIdentifier { get; set; }
}

public class CreateSettingRequest
{
    [JsonPropertyName("UserIdentifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("DefaultDownloadPath")]
    public string DefaultDownloadPath { get; set; }
    
    [JsonPropertyName("DarkModeEnabled")]
    public bool DarkModeEnabled { get; set; }
    
    [JsonPropertyName("ServerUrl")]
    public string? ServerUrl { get; set; }
    
    [JsonPropertyName("ScanFolderOnStartup")]
    public bool ScanFolderOnStartup { get; set; }
}

public class LoginRequest
{
    [JsonPropertyName("Username")]
    public string Username { get; set; }
    
    [JsonPropertyName("Password")]
    public string Password { get; set; }
}
