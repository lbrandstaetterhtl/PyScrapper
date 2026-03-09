using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Avalonia.Media.Imaging;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

public class ApiClient
{
    private readonly AppLogger _logger = new();

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public async Task<string> SendScrapRequest(DownloadRequestData requestData, string serverUrl)
    {
        HttpClient client = new();
        
        client.Timeout = TimeSpan.FromMinutes(30);

        
        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"http://{serverUrl}/download", content);
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var deserializedResponse = JsonSerializer.Deserialize<NormalResponse>(responseData, JsonOptions);

            var log = new Massage($"Download successful for URL: \"{requestData.Url}\", saved to: {deserializedResponse?.Message}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Id!;
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Massage($"Download failed for URL: \"{requestData.Url}\", error: " + deserializedError?.Detail, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            return "-1";
        }
    }

    public async Task<HealthResponse> GetHealth(string serverUrl)
    {
        HttpClient client = new();

        var response = await client.GetAsync($"http://{serverUrl}/health");
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var health = JsonSerializer.Deserialize<HealthResponse>(responseData, JsonOptions);

            var text =
                $"Server health check successful: Uptime {health?.UptimeSeconds} seconds, Memory {health?.MemoryMb} MB, PID {health?.Pid}, Processes {health?.Processes.Count}";

            var log = new Massage(text, DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return health;
        }
        else
        {
            var errorResponse = JsonSerializer.Deserialize<HealthErrorResponse>(responseData, JsonOptions);

            var log = new Massage(errorResponse?.msg ?? "Server health check failed", DateTime.Now,
                errorResponse?.type ?? "ERROR");
            _logger.LogNewMassage(log);
            
            return null;
        }
    }
    
    public async Task<List<YoutubeVideoItem>> SendSearchRequest(SearchRequestData requestData, string serverUrl)
    {
        HttpClient client = new();

        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"http://{serverUrl}/search", content);
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var deserializedResponse = JsonSerializer.Deserialize<SearchSuccessResponse>(responseData, JsonOptions);

            var log = new Massage($"Search successful for query: \"{deserializedResponse?.Query}\", found {deserializedResponse?.Results.Count} results", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Results ?? new List<YoutubeVideoItem>();
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Massage($"Search failed for query: \"{requestData.Search}\", error: " + deserializedError?.Detail, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);
            
            return new List<YoutubeVideoItem>();
        }
    }
    
    public async Task<ProgressSuccessResponse> GetDownloadProgress(string downloadId, string serverUrl)
    {
        HttpClient client = new();

        var response = await client.GetAsync($"http://{serverUrl}/download/progress/{downloadId}");
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var progressResponse = JsonSerializer.Deserialize<ProgressSuccessResponse>(responseData, JsonOptions);

            var log = new Massage($"Download progress for ID: \"{downloadId}\": {progressResponse?.Status}, {progressResponse?.DownloadProgress}%, {progressResponse?.Speed} MB/s", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return progressResponse;
        }
        else
        {
            
            var errorResponse = JsonSerializer.Deserialize<ProgressErrorResponse>(responseData, JsonOptions);

            var log = new Massage(errorResponse?.Message!, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);

            return null;
        }
    }

    public class HealthErrorResponse
    {
        [JsonPropertyName("msg")]
        public string msg { get; set; }
        
        [JsonPropertyName("type")]
        public string type { get; set; }
    }

    public class DownloadRequestData
    {
        [JsonPropertyName("provider")]
        public string Provider { get; set; }
        
        [JsonPropertyName("url")]
        public string Url { get; set; }
        
        [JsonPropertyName("mediatype")]
        public string Mediatype { get; set; }
        
        [JsonPropertyName("download_path")]
        public string Download_path { get; set; }
    }

    public class ServerProcess
    {
        public int Pid { get; set; }
        public string Name { get; set; }
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
        public List<ServerProcess> Processes { get; set; }
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

    public class YoutubeVideoItem
    {
        public string videoId { get; set; }
        public string url { get; set; }
        public string thumbnail { get; set; }
        public Bitmap ThumbnailBitmap { get; set; }
        public string title { get; set; }
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
        
        [JsonPropertyName("fileName")]
        public string FileName { get; set; }
    }
    
    public class ProgressErrorResponse
    {
        [JsonPropertyName("message")]
        public string Message { get; set; }
    }
    
    public class SearchSuccessResponse
    {
        [JsonPropertyName("provider")]
        public string Provider { get; set; }
        
        [JsonPropertyName("query")]
        public string Query { get; set; }
        
        [JsonPropertyName("results")]
        public List<YoutubeVideoItem> Results { get; set; }
    }

    public class HttpErrorResponse
    {
        [JsonPropertyName("detail")] 
        public string Detail { get; set; }
    }

}