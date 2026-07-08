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
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("url")]
    public string Url { get; set; }
    
    [JsonPropertyName("download_path")]
    public string DownloadPath { get; set; }
    
    [JsonPropertyName("media_type")]
    public string MediaType { get; set; }
    
    [JsonPropertyName("downloaded_at")]
    public string DownloadedAt { get; set; }
    
    [JsonPropertyName("is_playable")]
    public bool IsPlayable { get; set; }
    
    [JsonPropertyName("title")]
    public string Title { get; set; }
}

public class CreatePlaylistRequest
{
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("name")]
    public string Name { get; set; }
    
    [JsonPropertyName("description")]
    public string Description { get; set; }
}

public class CreatePlaylistMediaRequest
{
    [JsonPropertyName("playlist_identifier")]
    public string PlaylistIdentifier { get; set; }
    
    [JsonPropertyName("media_identifier")]
    public string MediaIdentifier { get; set; }
}

public class CreateSettingRequest
{
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("default_download_path")]
    public string DefaultDownloadPath { get; set; }
    
    [JsonPropertyName("dark_mode_enabled")]
    public bool DarkModeEnabled { get; set; }
    
    [JsonPropertyName("server_url")]
    public string? ServerUrl { get; set; }
    
    [JsonPropertyName("scan_folder_on_startup")]
    public bool ScanFolderOnStartup { get; set; }
}

public class LoginRequest
{
    [JsonPropertyName("username")]
    public string Username { get; set; }
    
    [JsonPropertyName("password")]
    public string Password { get; set; }
}
