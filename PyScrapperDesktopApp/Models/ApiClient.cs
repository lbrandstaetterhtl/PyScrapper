using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace PyScrapperDesktopApp.Models;

public class ApiClient
{
    private readonly AppLogger _logger = new();

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public async Task SendScrapRequest(RequestData requestData, string serverUrl)
    {
        HttpClient client = new();

        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"http://{serverUrl}/download", content);
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var successResponse = JsonSerializer.Deserialize<SuccessResponse>(responseData, JsonOptions);

            var downloadedMedia =
                new DownloadedMedia(requestData.Url, requestData.MediaType, DateTime.Now, "N/A", false);
            downloadedMedia.SetHighestId(AppData.DownloadedMedias);
            AppData.AddDownloadedMedia(downloadedMedia);

            var log = new Massage(successResponse?.Message ?? "Scraping successful", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
        }
        else
        {
            var errorResponse = JsonSerializer.Deserialize<ErrorResponse>(responseData, JsonOptions);

            var log = new Massage(errorResponse?.msg ?? "Scraping failed", DateTime.Now,
                errorResponse?.type ?? "ERROR");
            _logger.LogNewMassage(log);
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
            var errorResponse = JsonSerializer.Deserialize<ErrorResponse>(responseData, JsonOptions);

            var log = new Massage(errorResponse?.msg ?? "Server health check failed", DateTime.Now,
                errorResponse?.type ?? "ERROR");
            _logger.LogNewMassage(log);
        }

        return null;
    }

    public class RequestData
    {
        public string Provider { get; set; }
        public string Url { get; set; }
        public string MediaType { get; set; }
    }

    public class ErrorResponse
    {
        [JsonPropertyName("msg")] public string msg { get; set; }

        [JsonPropertyName("type")] public string type { get; set; }
    }

    public class SuccessResponse
    {
        public string Message { get; set; }
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
}