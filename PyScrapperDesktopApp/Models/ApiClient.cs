using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

public class ApiClient
{
    private readonly AppLogger _logger = new();

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public async Task<bool> SendScrapRequest(DownloadRequestData requestData, string serverUrl)
    {
        HttpClient client = new();
        
        client.Timeout = TimeSpan.FromMinutes(30);

        
        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        _logger.LogNewMassage(new Massage($"[DEBUG] Sending JSON: {jsonContent}", DateTime.Now, "DEBUG"));
        _logger.LogNewMassage(new Massage($"[DEBUG] Server URL: http://{serverUrl}/download", DateTime.Now, "DEBUG"));
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"http://{serverUrl}/download", content);
        var responseData = await response.Content.ReadAsStringAsync();
        _logger.LogNewMassage(new Massage($"[DEBUG] Response status: {response.StatusCode}", DateTime.Now, "DEBUG"));
        _logger.LogNewMassage(new Massage($"[DEBUG] Response body: {responseData}", DateTime.Now, "DEBUG"));
        
        
        try
        {
            var deserializedResponse = JsonSerializer.Deserialize<DownloadSuccessResponse>(responseData, JsonOptions);

            if (deserializedResponse.Status == "error")
            {
                throw new Exception("Download request failed with error status");
            }

            bool isPlayable = File.Exists(deserializedResponse.Message.File);

            var downloadedMedia =
                new DownloadedMedia(requestData.Url, requestData.Mediatype, DateTime.Now, deserializedResponse.Message.File, isPlayable, deserializedResponse.Message.identifier);
            downloadedMedia.SetHighestId(AppData.DownloadedMedias);
            AppData.AddDownloadedMedia(downloadedMedia);

            var log = new Massage($"{deserializedResponse?.Message.Raw_status}, saved to {downloadedMedia.DownloadPath}", DateTime.Now,
                deserializedResponse?.Message.Raw_status.Contains("complete", StringComparison.OrdinalIgnoreCase) == true ? "INFO" : "WARNING");
            _logger.LogNewMassage(log);
            
            return true;
        }
        catch (Exception e)
        {
            var deserializedError = JsonSerializer.Deserialize<DownloadErrorResponse>(responseData, JsonOptions);
            var log = new Massage("Scraping failed, server gave error: " + deserializedError?.Message.Error + $", scrap url: {requestData.Url}, Download path: {requestData.Download_path}", DateTime.Now,
                deserializedError?.Message.Error.Contains("complete", StringComparison.OrdinalIgnoreCase) == true ? "INFO" : "ERROR");
            _logger.LogNewMassage(log);
            
            return false;
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
        }

        return null;
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

            var log = new Massage($"Search successful for query: {deserializedResponse?.Message.query}, found {deserializedResponse?.Message.results.Count} results", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Message.results ?? new List<YoutubeVideoItem>();
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<SearchErrorResponse>(responseData, JsonOptions);
            var log = new Massage("Search failed for query: " + deserializedError?.Message.Query + ", error: " + deserializedError?.Message.Error, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);
            
            return new List<YoutubeVideoItem>();
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
    

    public class DownloadSuccessResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }
        
        [JsonPropertyName("jobtype")]
        public string JobType { get; set; }
        
        [JsonPropertyName("status")]
        public string Status { get; set; }
        
        [JsonPropertyName("message")]
        public DownloadSuccessMessage Message { get; set; }
    }
    
    public class DownloadErrorResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }
        
        [JsonPropertyName("jobtype")]
        public string JobType { get; set; }
        
        [JsonPropertyName("status")]
        public string Status { get; set; }
        
        [JsonPropertyName("message")]
        public DonwloadErrorMessage Message { get; set; }
    }

    public class DownloadSuccessMessage
    {
        public string Provider { get; set; }
        public string identifier { get; set; }
        public string File { get; set; }
        public string Raw_status { get; set; }
    }
    
    public class DonwloadErrorMessage
    {
        public string Error { get; set; }
        public string Url { get; set; }
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

    public class SearchSuccessResponse
    {
        [JsonPropertyName("id")]
        public string VideoId { get; set; }
        
        [JsonPropertyName("jobtype")]
        public string Jobtype { get; set; }
        
        [JsonPropertyName("status")]
        public string Status { get; set; }
        
        [JsonPropertyName("message")]
        public SearchResponseMessage Message { get; set; }
    }
    
    public class SearchResponseMessage
    {
        public string provider { get; set; }
        public string query { get; set; }
        public List<YoutubeVideoItem> results { get; set; }
    }

    public class YoutubeVideoItem
    {
        public string videoId { get; set; }
        public string url { get; set; }
        public string thumbnail { get; set; }
        public string title { get; set; }
    }
    
    public class SearchErrorResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }
        
        [JsonPropertyName("jobtype")]
        public string JobType { get; set; }
        
        [JsonPropertyName("status")]
        public string Status { get; set; }
        
        [JsonPropertyName("message")]
        public SearchErrorMessage Message { get; set; }
    }
    
    public class SearchErrorMessage
    {
        public string Error { get; set; }
        public string Query { get; set; }
    }
}