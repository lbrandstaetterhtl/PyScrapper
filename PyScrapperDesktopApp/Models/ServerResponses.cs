using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PyScrapperDesktopApp.Models;

public class HealthErrorResponse
{
    [JsonPropertyName("msg")]
    public string msg { get; set; }
    
    [JsonPropertyName("type")]
    public string type { get; set; }
}
    
public class HealthResponse
{
    [JsonPropertyName("ok")]
        public bool Ok { get; set; }
        
    [JsonPropertyName("uptime_seconds")]
        public double UptimeSeconds { get; set; }
        
    [JsonPropertyName("memory_mb")]
        public double MemoryMb { get; set; }
        
    [JsonPropertyName("pid")]
    public int Pid { get; set; }
        
    [JsonPropertyName("processes")]
    public List<ApiClient.ServerProcess> Processes { get; set; }
        
    [JsonPropertyName("active_downloads")]
    public List<ApiClient.DownloadJobItem> ActiveDownloads { get; set; }
        
    [JsonPropertyName("error_messages")]
    public List<string> ErrorMessages { get; set; }
}

public class NormalResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; }
        
    [JsonPropertyName("message")]
    public string Message { get; set; }
}

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
}

public class SearchSuccessResponse
{
    [JsonPropertyName("provider")]
    public string Provider { get; set; }
        
    [JsonPropertyName("query")]
    public string Query { get; set; }
        
    [JsonPropertyName("results")]
    public List<ApiClient.SearchResultItem> Results { get; set; }
}

public class HttpErrorResponse
{
    [JsonPropertyName("detail")] 
    public string Detail { get; set; }
}