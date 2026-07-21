using System.Text.Json;
using PyScrapperDesktopApp.Models;
using Xunit;
using static PyScrapperDesktopApp.Models.ApiClient;
using HealthResponse = PyScrapperDesktopApp.Models.HealthResponse;

namespace PyScrapperDesktopApp.Tests.Models;

public class ApiClientDtoTests
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    #region DownloadRequestData Tests

    [AvaloniaFact]
    public void DownloadRequestData_Serialization_UsesJsonPropertyNames()
    {
        var request = new DownloadRequestData
        {
            Provider = "youtube",
            Url = "https://youtube.com/watch?v=abc",
            Mediatype = ".mp3",
            Download_path = @"C:\Downloads"
        };

        var json = JsonSerializer.Serialize(request, JsonOptions);

        Assert.Contains("\"provider\"", json);
        Assert.Contains("\"url\"", json);
        Assert.Contains("\"mediatype\"", json);
        Assert.Contains("\"download_path\"", json);
        Assert.Contains("youtube", json);
    }

    [AvaloniaFact]
    public void DownloadRequestData_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "provider": "suno",
            "url": "https://suno.com/song/123",
            "mediatype": ".mp4",
            "download_path": "/tmp/downloads"
        }
        """;

        var data = JsonSerializer.Deserialize<DownloadRequestData>(json, JsonOptions);

        Assert.NotNull(data);
        Assert.Equal("suno", data.Provider);
        Assert.Equal("https://suno.com/song/123", data.Url);
        Assert.Equal(".mp4", data.Mediatype);
        Assert.Equal("/tmp/downloads", data.Download_path);
    }

    #endregion

    #region NormalResponse Tests

    [AvaloniaFact]
    public void NormalResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "job-1",
            "message": "Download started successfully"
        }
        """;

        var response = JsonSerializer.Deserialize<NormalResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("job-1", response.Id);
        Assert.Equal("Download started successfully", response.Message);
    }

    [AvaloniaFact]
    public void NormalResponse_ErrorDeserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "-1",
            "message": "Video not found"
        }
        """;

        var response = JsonSerializer.Deserialize<NormalResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("-1", response.Id);
        Assert.Equal("Video not found", response.Message);
    }

    [AvaloniaFact]
    public void NormalResponse_Serialization_UsesJsonPropertyNames()
    {
        var response = new NormalResponse
        {
            Id = "test-id",
            Message = "test message"
        };

        var json = JsonSerializer.Serialize(response, JsonOptions);

        Assert.Contains("\"id\"", json);
        Assert.Contains("\"message\"", json);
    }

    [AvaloniaFact]
    public void NormalResponse_RoundTrip_PreservesData()
    {
        var original = new NormalResponse
        {
            Id = "round-trip-id",
            Message = "round trip message"
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<NormalResponse>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Id, deserialized.Id);
        Assert.Equal(original.Message, deserialized.Message);
    }

    #endregion

    #region HealthResponse Tests

    [AvaloniaFact]
    public void HealthResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "ok": true,
            "uptime_seconds": 3600.5,
            "memory_mb": 256.3,
            "pid": 12345,
            "processes": [
                {"Pid": 111, "Name": "ffmpeg"},
                {"Pid": 222, "Name": "yt-dlp"}
            ]
        }
        """;

        var response = JsonSerializer.Deserialize<HealthResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.True(response.Ok);
        Assert.Equal(3600.5, response.UptimeSeconds);
        Assert.Equal(256.3, response.MemoryMb);
        Assert.Equal(12345, response.Pid);
        Assert.NotNull(response.Processes);
        Assert.Equal(2, response.Processes.Count);
        Assert.Equal("ffmpeg", response.Processes[0].Name);
        Assert.Equal(111, response.Processes[0].Pid);
    }

    [AvaloniaFact]
    public void HealthResponse_EmptyProcesses_DeserializesCorrectly()
    {
        var json = """
        {
            "ok": true,
            "uptime_seconds": 10.0,
            "memory_mb": 50.0,
            "pid": 1,
            "processes": []
        }
        """;

        var response = JsonSerializer.Deserialize<HealthResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Empty(response.Processes);
    }

    #endregion

    #region HealthErrorResponse Tests

    [AvaloniaFact]
    public void HealthErrorResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "msg": "Server is unavailable",
            "type": "ERROR"
        }
        """;

        var response = JsonSerializer.Deserialize<HealthErrorResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("Server is unavailable", response.msg);
        Assert.Equal("ERROR", response.type);
    }

    #endregion

    #region SearchRequestData Tests

    [AvaloniaFact]
    public void SearchRequestData_Serialization_UsesJsonPropertyNames()
    {
        var request = new SearchRequestData
        {
            Provider = "youtube",
            Search = "funny cats",
            Top = 5
        };

        var json = JsonSerializer.Serialize(request, JsonOptions);

        Assert.Contains("\"provider\"", json);
        Assert.Contains("\"search\"", json);
        Assert.Contains("\"top\"", json);
        Assert.Contains("youtube", json);
        Assert.Contains("funny cats", json);
    }

    [AvaloniaFact]
    public void SearchRequestData_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "provider": "youtube",
            "search": "music video",
            "top": 10
        }
        """;

        var data = JsonSerializer.Deserialize<SearchRequestData>(json, JsonOptions);

        Assert.NotNull(data);
        Assert.Equal("youtube", data.Provider);
        Assert.Equal("music video", data.Search);
        Assert.Equal(10, data.Top);
    }

    #endregion

    #region SearchSuccessResponse Tests

    [AvaloniaFact]
    public void SearchSuccessResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "provider": "youtube",
            "query": "test query",
            "results": [
                {
                    "identifier": "abc123",
                    "url": "https://youtube.com/watch?v=abc123",
                    "thumbnail": "https://img.youtube.com/vi/abc123/0.jpg",
                    "title": "Test Video"
                }
            ]
        }
        """;

        var response = JsonSerializer.Deserialize<SearchSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("youtube", response.Provider);
        Assert.Equal("test query", response.Query);
        Assert.NotNull(response.Results);
        Assert.Single(response.Results);
        Assert.Equal("abc123", response.Results[0].identifier);
        Assert.Equal("Test Video", response.Results[0].title);
    }

    [AvaloniaFact]
    public void SearchSuccessResponse_EmptyResults_DeserializesCorrectly()
    {
        var json = """
        {
            "provider": "youtube",
            "query": "no results query",
            "results": []
        }
        """;

        var response = JsonSerializer.Deserialize<SearchSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("no results query", response.Query);
        Assert.NotNull(response.Results);
        Assert.Empty(response.Results);
    }

    [AvaloniaFact]
    public void SearchSuccessResponse_MultipleResults_DeserializesCorrectly()
    {
        var json = """
        {
            "provider": "youtube",
            "query": "music",
            "results": [
                {
                    "identifier": "id1",
                    "url": "https://youtube.com/watch?v=id1",
                    "thumbnail": "https://img.youtube.com/vi/id1/0.jpg",
                    "title": "Song 1"
                },
                {
                    "identifier": "id2",
                    "url": "https://youtube.com/watch?v=id2",
                    "thumbnail": "https://img.youtube.com/vi/id2/0.jpg",
                    "title": "Song 2"
                }
            ]
        }
        """;

        var response = JsonSerializer.Deserialize<SearchSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal(2, response.Results.Count);
        Assert.Equal("id1", response.Results[0].identifier);
        Assert.Equal("id2", response.Results[1].identifier);
    }

    #endregion

    #region ProgressSuccessResponse Tests

    [AvaloniaFact]
    public void ProgressSuccessResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "dl-123",
            "status": "downloading",
            "downloadProgress": 45.5,
            "errorMessage": null,
            "totalBytes": 10485760,
            "downloadedBytes": 4770816,
            "speed": 1024.5,
            "fileName": "video.mp4"
        }
        """;

        var response = JsonSerializer.Deserialize<ProgressSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("dl-123", response.Id);
        Assert.Equal("downloading", response.Status);
        Assert.Equal(45.5f, response.DownloadProgress);
        Assert.Null(response.ErrorMessage);
        Assert.Equal(10485760L, response.TotalBytes);
        Assert.Equal(4770816L, response.DownloadedBytes);
        Assert.Equal(1024.5f, response.Speed);
    }

    [AvaloniaFact]
    public void ProgressSuccessResponse_CompletedDownload_DeserializesCorrectly()
    {
        var json = """
        {
            "id": "dl-456",
            "status": "complete",
            "downloadProgress": 100.0,
            "errorMessage": null,
            "totalBytes": 5242880,
            "downloadedBytes": 5242880,
            "speed": 0.0,
            "fileName": "audio.mp3"
        }
        """;

        var response = JsonSerializer.Deserialize<ProgressSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("complete", response.Status);
        Assert.Equal(100.0f, response.DownloadProgress);
        Assert.Equal(response.TotalBytes, response.DownloadedBytes);
    }

    [AvaloniaFact]
    public void ProgressSuccessResponse_WithError_DeserializesCorrectly()
    {
        var json = """
        {
            "id": "dl-789",
            "status": "error",
            "downloadProgress": 0.0,
            "errorMessage": "Connection timeout",
            "totalBytes": 0,
            "downloadedBytes": 0,
            "speed": 0.0,
            "fileName": ""
        }
        """;

        var response = JsonSerializer.Deserialize<ProgressSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("error", response.Status);
        Assert.Equal("Connection timeout", response.ErrorMessage);
        Assert.Equal(0f, response.DownloadProgress);
    }

    [AvaloniaFact]
    public void ProgressSuccessResponse_Properties_CanBeSetAndRead()
    {
        var response = new ProgressSuccessResponse
        {
            Id = "test-id",
            Status = "downloading",
            DownloadProgress = 75.3f,
            ErrorMessage = null,
            TotalBytes = 20000000,
            DownloadedBytes = 15060000,
            Speed = 2048.0f,
        };

        Assert.Equal("test-id", response.Id);
        Assert.Equal("downloading", response.Status);
        Assert.Equal(75.3f, response.DownloadProgress);
        Assert.Null(response.ErrorMessage);
        Assert.Equal(20000000L, response.TotalBytes);
        Assert.Equal(15060000L, response.DownloadedBytes);
        Assert.Equal(2048.0f, response.Speed);
    }

    #endregion
    
    #region YoutubeVideoItem Tests

    [AvaloniaFact]
    public void YoutubeVideoItem_Properties_CanBeSetAndRead()
    {
        var item = new SearchResultItem()
        {
            identifier = "XPwUIDYKHX4",
            url = "https://youtube.com/watch?v=XPwUIDYKHX4",
            thumbnail = "https://img.youtube.com/vi/XPwUIDYKHX4/0.jpg",
            title = "Test Video Title"
        };

        Assert.Equal("XPwUIDYKHX4", item.identifier);
        Assert.Equal("https://youtube.com/watch?v=XPwUIDYKHX4", item.url);
        Assert.Equal("https://img.youtube.com/vi/XPwUIDYKHX4/0.jpg", item.thumbnail);
        Assert.Equal("Test Video Title", item.title);
        Assert.Null(item.ThumbnailBitmap); // Not set from JSON
    }

    #endregion

    #region ServerProcess Tests

    [AvaloniaFact]
    public void ServerProcess_Properties_CanBeSetAndRead()
    {
        var process = new ServerProcess
        {
            Pid = 12345,
            Name = "ffmpeg"
        };

        Assert.Equal(12345, process.Pid);
        Assert.Equal("ffmpeg", process.Name);
    }

    #endregion

    #region Roundtrip Serialization Tests

    [AvaloniaFact]
    public void DownloadRequestData_RoundTrip_PreservesData()
    {
        var original = new DownloadRequestData
        {
            Provider = "youtube",
            Url = "https://youtube.com/watch?v=abc",
            Mediatype = ".mp3",
            Download_path = @"C:\Downloads"
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<DownloadRequestData>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Provider, deserialized.Provider);
        Assert.Equal(original.Url, deserialized.Url);
        Assert.Equal(original.Mediatype, deserialized.Mediatype);
        Assert.Equal(original.Download_path, deserialized.Download_path);
    }

    [AvaloniaFact]
    public void SearchRequestData_RoundTrip_PreservesData()
    {
        var original = new SearchRequestData
        {
            Provider = "youtube",
            Search = "test search",
            Top = 15
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<SearchRequestData>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Provider, deserialized.Provider);
        Assert.Equal(original.Search, deserialized.Search);
        Assert.Equal(original.Top, deserialized.Top);
    }

    [AvaloniaFact]
    public void ProgressSuccessResponse_RoundTrip_PreservesData()
    {
        var original = new ProgressSuccessResponse
        {
            Id = "rt-id",
            Status = "downloading",
            DownloadProgress = 55.5f,
            ErrorMessage = null,
            TotalBytes = 1000000,
            DownloadedBytes = 555000,
            Speed = 512.0f,
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<ProgressSuccessResponse>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Id, deserialized.Id);
        Assert.Equal(original.Status, deserialized.Status);
        Assert.Equal(original.DownloadProgress, deserialized.DownloadProgress);
        Assert.Equal(original.ErrorMessage, deserialized.ErrorMessage);
        Assert.Equal(original.TotalBytes, deserialized.TotalBytes);
        Assert.Equal(original.DownloadedBytes, deserialized.DownloadedBytes);
        Assert.Equal(original.Speed, deserialized.Speed);
    }

    #endregion
}


