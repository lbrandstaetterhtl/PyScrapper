using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Class representing the structure of an error response from the server, containing properties for the error message and type.
/// </summary>
public class HealthErrorResponse
{
    [JsonPropertyName("msg")]
    public string msg { get; set; }
    
    [JsonPropertyName("type")]
    public string type { get; set; }
}

/// <summary>
/// Class representing the structure of a health check response from the server, containing properties for the server's status, uptime, memory usage, process ID, active processes, active downloads, and any error messages.
/// This class is used to serialize and deserialize JSON data for health check responses from the server, providing detailed information about the server's current state and any issues it may be experiencing.
/// </summary>
public class HealthResponse
{
    [JsonPropertyName("ok")]
        public bool Ok { get; set; }
        
    [JsonPropertyName("uptime_seconds")]
        public double UptimeSeconds { get; set; }
        
    [JsonPropertyName("memory_mb")]
        public double? MemoryMb { get; set; }
        
    [JsonPropertyName("pid")]
    public int Pid { get; set; }
        
    [JsonPropertyName("processes")]
    public List<ApiClient.ServerProcess> Processes { get; set; }
        
    [JsonPropertyName("active_downloads")]
    public List<ApiClient.DownloadJobItem> ActiveDownloads { get; set; }
        
    [JsonPropertyName("error_messages")]
    public List<string> ErrorMessages { get; set; }
}

/// <summary>
/// Class representing the structure of a normal response from the server, containing properties for an identifier and a message.
/// This class is used to serialize and deserialize JSON data for standard responses from the server that do not fit into specific categories like health checks or search results.
/// </summary>
public class NormalResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; }
        
    [JsonPropertyName("message")]
    public string Message { get; set; }
}

/// <summary>
/// Class representing the structure of a progress response from the server, containing properties for an identifier, status, download progress, error message, total bytes, downloaded bytes, and download speed.
/// This class is used to serialize and deserialize JSON data for responses from the server that provide updates on the progress of a download job, allowing the client to track the status and performance of ongoing downloads
/// </summary>
public class ProgressSuccessResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; }
        
    [JsonPropertyName("status")]
    public string Status { get; set; }
        
    [JsonPropertyName("downloadProgress")]
    public float DownloadProgress { get; set; }
        
    [JsonPropertyName("errorMessage")]
    public string ErrorMessage { get; set; }
        
    [JsonPropertyName("totalBytes")]
    public long TotalBytes { get; set; }
        
    [JsonPropertyName("downloadedBytes")]
    public long DownloadedBytes { get; set; }
        
    [JsonPropertyName("speed")]
    public float Speed { get; set; }
    
    [JsonPropertyName("eta")]
    public float Eta { get; set; }
    
    [JsonPropertyName("totalSegments")]
    public int TotalSegments { get; set; }
    
    [JsonPropertyName("downloadedSegments")]
    public int DownloadedSegments { get; set; }
}

/// <summary>
/// Class representing the structure of a search response from the server, containing properties for the provider, search query, and a list of search result items.
/// This class is used to serialize and deserialize JSON data for responses from the server that provide search results based on a search query, allowing the client to display relevant results to the user based on their search criteria and the specified provider.
/// Each search result item in the list contains details about an individual search result, such as the title, URL, and other relevant information depending on the provider and the type of media being searched for (e.g., video, audio, etc.).
/// </summary>
public class SearchSuccessResponse
{
    [JsonPropertyName("provider")]
    public string Provider { get; set; }
        
    [JsonPropertyName("query")]
    public string Query { get; set; }
        
    [JsonPropertyName("results")]
    public List<ApiClient.SearchResultItem> Results { get; set; }
}

/// <summary>
/// Class representing the structure of an error response from the server, containing a property for the error detail message.
/// This class is used to serialize and deserialize JSON data for error responses from the server, allowing the client to display meaningful error messages to the user when a request fails or encounters an issue on the server side.
/// The "detail" property provides specific information about the error that occurred, which can help the user understand what went wrong and potentially how to resolve the issue.
/// </summary>
public class HttpErrorResponse
{
    [JsonPropertyName("detail")] 
    public string Detail { get; set; }
}

public class CreateResponse
{
    [JsonPropertyName("message")]
    public string Message { get; set; }
    
    [JsonPropertyName("identifier")]
    public string Identifier { get; set; }
}

public class CreatePlaylistMediaResponse
{
    [JsonPropertyName("message")]
    public string Message { get; set; }
    
    [JsonPropertyName("position")]
    public int Position { get; set; }
}

/// <summary>
/// Class representing the structure of a default database response from the server, containing properties for a message and an identifier.
/// This class is used to serialize and deserialize JSON data for standard database responses from the server, allowing the client to receive confirmation messages and unique identifiers for newly created or modified database entries.
/// The "message" property provides information about the outcome of the database operation, while the "identifier" property contains a unique identifier associated with the database entry, which can be used for further operations or reference.
/// </summary>
public class DefaultDbResponse
{
    [JsonPropertyName("message")]
    public string Message { get; set; }
    
    [JsonPropertyName("identifier")]
    public string Identifier { get; set; }
}

/// <summary>
/// Class representing the structure of a response from the server when retrieving a playlist, containing properties for the playlist's identifier,
/// user identifier, name, and description. This class is used to serialize and deserialize JSON data for responses from the server that provide information about a specific playlist,
/// allowing the client to display the playlist's details to the user.
/// The "identifier" property uniquely identifies the playlist, the "userIdentifier" property indicates the user who owns the playlist,
/// the "name" property provides the name of the playlist, and the "description" property contains a brief description of the playlist's content or purpose.
/// </summary>
public class GetPlaylistResponse
{
    [JsonPropertyName("Identifier")]
    public string Identifier { get; set; }
    
    [JsonPropertyName("UserIdentifier")]
    public string UserIdentifier { get; set; }
    
    [JsonPropertyName("Name")]
    public string Name { get; set; }
    
    [JsonPropertyName("Description")]
    public string Description { get; set; }
}