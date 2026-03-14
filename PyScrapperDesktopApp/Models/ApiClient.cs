using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
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

            var log = new Massage($"Server received request and sent message: {deserializedResponse?.Message}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Id!;
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Massage($"Error sending download request. Server gave error: " + deserializedError?.Detail, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var massageBox = new MessageBox($"Error sending download request: {deserializedError?.Detail}");
            await massageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
            
            return "-1";
        }
    }

    public async Task<HealthResponse> GetHealth(string serverUrl, bool loogHealthResponse = true)
    {
        HttpClient client = new();

        var response = await client.GetAsync($"http://{serverUrl}/health");
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var health = JsonSerializer.Deserialize<HealthResponse>(responseData, JsonOptions);

            if (loogHealthResponse)
            {
                var text =
                    $"Server health check successful: Uptime {health?.UptimeSeconds} seconds, Memory {health?.MemoryMb} MB, PID {health?.Pid}, Processes {health?.Processes.Count}";

                var log = new Massage(text, DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }

            return health;
        }
        else
        {
            var errorResponse = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);

            var log = new Massage("Server gave this error while requesting health:" + errorResponse!.Detail, DateTime.Now,"ERROR");
            _logger.LogNewMassage(log);
            
            var massageBox = new MessageBox($"Error requesting server health: {errorResponse.Detail}");
            await massageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
            
            return null;
        }
    }
    
    public async Task<List<SearchResultItem>> SendSearchRequest(SearchRequestData requestData, string serverUrl)
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

            return deserializedResponse?.Results ?? new List<SearchResultItem>();
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Massage($"Search failed for query: \"{requestData.Search}\", error: " + deserializedError?.Detail, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);
            
            return new List<SearchResultItem>();
        }
    }
    
    public async Task<ProgressSuccessResponse> GetDownloadProgress(string downloadId, string serverUrl)
    {
        HttpClient client = new();

        var response = await client.GetAsync($"http://{serverUrl}/download/progress/{downloadId}");
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            try
            {
                var progressResponse = JsonSerializer.Deserialize<ProgressSuccessResponse>(responseData, JsonOptions);

                var log = new Massage(
                    $"Download progress for ID: \"{downloadId}\": {progressResponse?.Status}, {progressResponse?.DownloadProgress}%, {progressResponse?.Speed} MB/s",
                    DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                return progressResponse;
            }
            catch (Exception ex)
            {
                var log = new Massage($"Error parsing progress response for ID: \"{downloadId}\": {ex.Message}", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                return null;
            }
        }
        else
        {
            
            var errorResponse = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);

            var log = new Massage(errorResponse?.Detail!, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);

            return null;
        }
    }

    public class ServerProcess
    {
        public int Pid { get; set; }
        public string Name { get; set; }
    }

    public class DownloadJobItem
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }
        
        [JsonPropertyName("status")]
        public string Status { get; set; }
        
        [JsonPropertyName("downloadProgress")]
        public float DownloadProgress { get; set; }
        
        [JsonPropertyName("errorMessage")]
        public string ErrorMessage { get; set; }
    }

    public class SearchResultItem
    {
        public string identifier { get; set; }
        public string url { get; set; }
        public string thumbnail { get; set; }
        public Bitmap ThumbnailBitmap { get; set; }
        public string title { get; set; }
    }
}