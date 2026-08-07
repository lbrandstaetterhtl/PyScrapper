using System.Collections.Generic;
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
    public string? Download_path { get; set; }
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
    
    [JsonPropertyName("filters")]
    public SearchFilter Filters { get; set; }
}

/// <summary>
/// Class representing the data structure for search filters, containing properties for the creator and a list of tags to filter search results.
/// This class is used to serialize and deserialize JSON data when applying filters to search requests.
/// </summary>
public class SearchFilter
{
    [JsonPropertyName("creator")]
    public string Creator { get; set; }
    
    [JsonPropertyName("tags")]
    public List<string> Tags { get; set; }
}

/// <summary>
/// Class representing the data structure for a request to create a downloaded media entry, containing properties for the user identifier, URL, download path,
/// media type, download timestamp, playability status, and title.
/// This class is used to serialize and deserialize JSON data when making requests to create downloaded media entries on the server.
/// </summary>
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

/// <summary>
/// Class representing the data structure for a request to create a playlist, containing properties for the user identifier, playlist name, and description.
/// This class is used to serialize and deserialize JSON data when making requests to create playlists on the server.
/// </summary>
public class CreatePlaylistRequest
{
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("name")]
    public string Name { get; set; }
    
    [JsonPropertyName("description")]
    public string Description { get; set; }
}

/// <summary>
/// Class representing the data structure for a request to add media to a playlist, containing properties for the playlist identifier and media identifier.
/// This class is used to serialize and deserialize JSON data when making requests to add media to playlists on the server.
/// </summary>
public class CreatePlaylistMediaRequest
{
    [JsonPropertyName("playlist_identifier")]
    public string PlaylistIdentifier { get; set; }
    
    [JsonPropertyName("media_identifier")]
    public string MediaIdentifier { get; set; }
}

/// <summary>
/// Class representing the data structure for a request to create user settings, containing properties for the user identifier,
/// default download path, dark mode preference, and scan folder on startup preference.
/// This class is used to serialize and deserialize JSON data when making requests to create user settings on the server.
/// </summary>
public class CreateSettingRequest
{
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("default_download_path")]
    public string DefaultDownloadPath { get; set; }
    
    [JsonPropertyName("dark_mode_enabled")]
    public bool DarkModeEnabled { get; set; }
    
    [JsonPropertyName("scan_folder_on_startup")]
    public bool ScanFolderOnStartup { get; set; }
}

/// <summary>
/// Class representing the data structure for a login request, containing properties for the username and password.
/// This class is used to serialize and deserialize JSON data when making login requests to the server.
/// </summary>
public class LoginRequest
{
    [JsonPropertyName("username")]
    public string Username { get; set; }
    
    [JsonPropertyName("password")]
    public string Password { get; set; }
}

/// <summary>
/// Class representing the data structure for a registration request, containing properties for the username and password.
/// This class is used to serialize and deserialize JSON data when making registration requests to the server.
/// </summary>
public class RegisterRequest
{
    [JsonPropertyName("username")]
    public string Username { get; set; }
    
    [JsonPropertyName("password")]
    public string Password { get; set; }
}

/// <summary>
/// Class representing the data structure for a request to save user data, containing properties for the user identifier, playlists, downloaded media, playlist media, and settings.
/// This class is used to serialize and deserialize JSON data when making requests to save user data on the server.
/// </summary>
public class SaveDataRequest
{
    [JsonPropertyName("user_identifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("playlists")]
    public List<Playlist> Playlists { get; set; }
    
    [JsonPropertyName("medias")]
    public List<DownloadedMedia> DownloadedMedias { get; set; }
    
    [JsonPropertyName("playlist_medias")]
    public List<PlaylistMedia> PlaylistMedias { get; set; }
    
    [JsonPropertyName("setting")]
    public Settings Setting { get; set; }
}
