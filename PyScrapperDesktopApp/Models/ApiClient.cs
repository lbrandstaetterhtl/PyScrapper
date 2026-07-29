using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Client for communicating with the server API.
/// It provides methods for sending scrap requests, getting server health, sending search requests, and getting download progress.
/// </summary>
public class ApiClient(DialogService dialogService) : Interfaces.IApiClient
{
    private readonly AppLogger _logger = AppLogger.Instance;

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    /// <summary>
    /// Sends a scrap request to the server and returns the download ID if successful, or "-1" if there was an error.
    /// Also logs the response from the server and shows a message box if there was an error.
    /// </summary>
    /// <param name="requestData"></param>
    /// <param name="ct"></param>
    /// <returns name="id"></returns>
    public async Task<string> SendScrapRequest(DownloadRequestData requestData)
    {
        using HttpClient client = new();
        
        client.Timeout = TimeSpan.FromMinutes(30);

        
        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/download", content);
        var responseData = await response.Content.ReadAsStringAsync();
        
        if (response.IsSuccessStatusCode)
        {
            var deserializedResponse = JsonSerializer.Deserialize<NormalResponse>(responseData, JsonOptions);

            var log = new Message($"Server received request and sent message: {deserializedResponse?.Message}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Id!;
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Message($"Error sending download request. Server gave error: " + deserializedError?.Detail, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var massageBox = new MessageBox($"Error sending download request: {deserializedError?.Detail}");
            await massageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
            
            return "-1";
        }
    }

    /// <summary>
    /// Gets the health of the server by sending a GET request to the /health endpoint. If successful, it logs the health information and returns a HealthResponse object.
    /// If there is an error, it logs the error and shows a message box with the error detail, then returns null.
    /// </summary>
    /// <param name="loogHealthResponse"></param>
    /// <param name="ct"></param>
    /// <returns name="health"></returns>
    public async Task<HealthResponse> GetHealth(bool loogHealthResponse = true)
    {
        try
        {

            using HttpClient client = new();

            var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/health");
            var responseData = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                try
                {
                    var health = JsonSerializer.Deserialize<HealthResponse>(responseData, JsonOptions);

                    if (loogHealthResponse)
                    {
                        var text =
                            $"Server health check successful: Uptime {health?.UptimeSeconds} seconds, Memory {health?.MemoryMb} MB, PID {health?.Pid}, Processes {health?.Processes.Count}";

                        var log = new Message(text, DateTime.Now, "INFO");
                        _logger.LogNewMassage(log);
                    }

                    return health;
                }
                catch (Exception ex)
                {
                    var log = new Message($"Error sending health request: {ex.Message}", DateTime.Now, "ERROR");
                    _logger.LogNewMassage(log);

                    return null;
                }
            }
            else
            {
                var errorResponse = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);

                var log = new Message("Server gave this error while requesting health:" + errorResponse!.Detail,
                    DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);

                var massageBox = new MessageBox($"Error requesting server health: {errorResponse.Detail}");
                await massageBox.ShowDialog(
                    App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop
                        ? desktop.MainWindow
                        : null);

                return null;
            }
        }
        catch (Exception ex)
        {
            var response = new HealthResponse()
            {
                Ok = false
            };
            return response;
        }
    }
    
    /// <summary>
    /// Sends a search request to the server with the given search parameters. If successful, it logs the number of results found and returns a list of SearchResultItem objects.
    /// If there is an error, it logs the error and shows a message box with the error detail, then returns an empty list. The search results include the identifier, url, thumbnail url, and title of each result.
    /// The thumbnail is also downloaded as a Bitmap and stored in the Thumbnail
    /// </summary>
    /// <param name="requestData"></param>
    /// <returns name="results"></returns>
    public async Task<List<SearchResultItem>> SendSearchRequest(SearchRequestData requestData)
    {
        using HttpClient client = new();

        var jsonContent = JsonSerializer.Serialize(requestData, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/search", content);
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var deserializedResponse = JsonSerializer.Deserialize<SearchSuccessResponse>(responseData, JsonOptions);

            var log = new Message($"Search successful for query: \"{deserializedResponse?.Query}\", found {deserializedResponse?.Results.Count} results", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            return deserializedResponse?.Results ?? new List<SearchResultItem>();
        }
        else
        {
            var deserializedError = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);
            var log = new Message($"Search failed for query: \"{requestData.Search}\", error: " + deserializedError?.Detail, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);
            
            return new List<SearchResultItem>();
        }
    }

    /// <summary>
    /// Gets the download progress for a given download ID by sending a GET request to the /download/progress/{downloadId} endpoint.
    /// If successful, it logs the progress information and returns a ProgressSuccessResponse object.
    /// If there is an error, it logs the error and shows a message box with the error detail, then returns null.
    /// The progress information includes the status, download progress percentage, download speed in MB/s, total bytes, and downloaded bytes.
    /// This information can be used to update the UI with the current progress of the download.
    /// </summary>
    /// <param name="downloadId"></param>
    /// <param name="ct"></param>
    /// <returns name="progressResponse"></returns>
    public async Task<ProgressSuccessResponse> GetDownloadProgress(string downloadId)
    {
        using HttpClient client = new();

        var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/download/progress/{downloadId}");
        var responseData = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            try
            {
                var progressResponse = JsonSerializer.Deserialize<ProgressSuccessResponse>(responseData, JsonOptions);

                var log = new Message(
                    $"Download progress for ID: \"{downloadId}\": {progressResponse?.Status}, {progressResponse?.DownloadProgress}%, {progressResponse?.Speed} MB/s",
                    DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                return progressResponse;
            }
            catch (Exception ex)
            {
                var log = new Message($"Error parsing progress response for ID: \"{downloadId}\": {ex.Message}", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                return null;
            }
        }
        else
        {
            
            var errorResponse = JsonSerializer.Deserialize<HttpErrorResponse>(responseData, JsonOptions);

            var log = new Message(errorResponse?.Detail!, DateTime.Now,
                "ERROR");
            _logger.LogNewMassage(log);

            return null;
        }
    }

    /// <summary>
    /// Sends a list of scrap requests to the server sequentially. For each request, it calls the SendScrapRequest method and waits for the result.
    /// If the result is "-1", it adds false to the results list.
    /// Otherwise, it shows a progress bar window and starts tracking the download progress using the ProgressBarWindowViewModel.
    /// Once the download is complete, it adds the result (true if successful, false if there was an error) to the results list.
    /// If any exception occurs during the process, it logs the error and returns null.
    /// </summary>
    /// <param name="requestDataList"></param>
    /// <param name="ct"></param>
    /// <returns></returns>
    /// <exception cref="Exception"></exception>
    public async Task<List<bool>> SendListScrapRequest(List<DownloadRequestData> requestDataList, CancellationToken ct)
    {
        using HttpClient client = new();

        client.Timeout = TimeSpan.FromMinutes(30);

        List<bool> results = new List<bool>();

        try
        {
            foreach (var requestData in requestDataList)
            {
                ct.ThrowIfCancellationRequested();
                
                var scrapResult = await SendScrapRequest(requestData);

                if (scrapResult != "-1")
                {
                    Task.Delay(2000).Wait();

                    var progressWindow = new ProgressBarWindow();
                    progressWindow.Show();

                    var vm = progressWindow.DataContext as ProgressBarWindowViewModel;

                    if (vm == null)
                    {
                        await dialogService.ShowAlertAsync(
                            "An error occurred while initializing the progress window.");
                        continue;
                    }

                    bool errorWhileDownloading = await vm.StartProgress(scrapResult);

                    if (!errorWhileDownloading)
                    {
                        await vm.WaitUntilFinished();

                        var userIdentifier = AppData.CurrentUser.Identifier;
                        var url = requestData.Url;
                        var mediaType = requestData.Mediatype;
                        var downloadFilePath = Path.Combine(requestData.Download_path ?? AppData.Settings.DownloadPath, requestData.Filename + mediaType);
                        var downloadedAt = DateTime.Now;
                        var isPlayable = File.Exists(downloadFilePath) && await AudioPlayer.IsSupportedCodec(downloadFilePath);
                        
                        var createRequest = new CreateDownloadedMediaRequest()
                        {
                            UserIdentifier = userIdentifier,
                            Url = url,
                            DownloadPath = downloadFilePath,
                            MediaType = mediaType,
                            DownloadedAt = downloadedAt.ToString("o"),
                            IsPlayable = isPlayable,
                            Title = requestData.Filename
                        };
                        
                        DownloadedMedia media = await Database.CreateDownloadedMedia(createRequest);
                        
                        AppData.AddDownloadedMedia(media);
                    }
                    else
                    {
                        await dialogService.ShowAlertAsync("Download failed, check logs for more details");
                    }
                }
            }
            
            return results;
        }
        catch (OperationCanceledException ex)
        {
            var log = new Message($"Scrap request cancelled: {ex.Message}", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return null;
        }
        catch (Exception ex)
        {
            var log = new Message($"Error sending scrap request: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public async Task<bool> Login(LoginRequest req)
    {
        using var client = new HttpClient();
        var jsonContent = JsonSerializer.Serialize(req, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/login", content);
        var responseData = await response.Content.ReadAsStringAsync();
        
        var deserializedResponse = JsonSerializer.Deserialize<DefaultDbResponse>(responseData, JsonOptions);
        
        if (response.IsSuccessStatusCode)
        {
            var log = new Message($"Login successful for user: \"{req.Username}\"", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            AppData.CurrentUser = await Database.GetUser(req.Username);
            AppData.Config.LastLoggedInUser = AppData.CurrentUser;
            
            return true;
        }
        else
        {
            var log = new Message($"Login failed for user: \"{req.Username}\", error: " + deserializedResponse?.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var massageBox = new MessageBox($"Login failed: {deserializedResponse?.Message}");
            await massageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
            
            return false;
        }
    }

    public async Task<bool> Register(RegisterRequest req)
    {
        using var client = new HttpClient();
        var jsonContent = JsonSerializer.Serialize(req, JsonOptions);
        var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/register", content);
        var responseData = await response.Content.ReadAsStringAsync();
        
        var deserializedResponse = JsonSerializer.Deserialize<DefaultDbResponse>(responseData, JsonOptions);
        
        if (response.IsSuccessStatusCode)
        {
            var log = new Message($"Registration successful for user: \"{req.Username}\"", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            return true;
        }
        else
        {
            var log = new Message($"Registration failed for user: \"{req.Username}\", error: " + deserializedResponse?.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            
            var massageBox = new MessageBox($"Registration failed: {deserializedResponse?.Message}");
            await massageBox.ShowDialog(App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop ? desktop.MainWindow : null);
            
            return false;
        }
    }

    /// <summary>
    /// ServerProcess represents a process running on the server, with its PID and name.
    /// This information is included in the health response from the server and can be used for monitoring and debugging purposes.
    /// </summary>
    public class ServerProcess
    {
        public int Pid { get; set; }
        public string Name { get; set; }
    }

    /// <summary>
    /// DownloadJobItem represents an active download job on the server, with its ID, status, download progress percentage, and any error message if applicable.
    /// </summary>
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

    /// <summary>
    /// SearchResultItem represents a single search result item returned from the server in response to a search request.
    /// It includes the identifier, url, thumbnail url, title, and a Bitmap of the thumbnail image.
    /// </summary>
    public class SearchResultItem
    {
        public string identifier { get; set; }
        public string url { get; set; }
        public string thumbnail { get; set; }
        public Bitmap ThumbnailBitmap { get; set; }
        public string title { get; set; }
    }
}