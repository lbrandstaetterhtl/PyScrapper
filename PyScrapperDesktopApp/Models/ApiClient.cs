using System;
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
            
            var log = new Massage(successResponse?.Message ?? "Scraping successful", DateTime.Now, "INFO");
            
            var downloadedMedia = new DownloadedMedia(requestData.Url, requestData.MediaType, DateTime.Now, "N/A", false);
            
            AppData.AddDownloadedMedia(downloadedMedia);
            
            _logger.LogNewMassage(log);
        }
        else
        {
            var errorResponse = JsonSerializer.Deserialize<ErrorResponse>(responseData, JsonOptions);
            
            var log = new Massage(errorResponse?.msg ?? "Scraping failed", DateTime.Now, errorResponse?.msg ?? "ERROR");
            
            _logger.LogNewMassage(log);
        }
    }
}

public class RequestData
{
    public string Provider { get; set; }
    public string Url { get; set; }
    public string MediaType { get; set; }
}

public class ErrorResponse
{
    [JsonPropertyName("msg")]
    public string msg { get; set; }
    
    [JsonPropertyName("type")]
    public string type { get; set; }
}

public class SuccessResponse
{
    public string Message { get; set; }
}